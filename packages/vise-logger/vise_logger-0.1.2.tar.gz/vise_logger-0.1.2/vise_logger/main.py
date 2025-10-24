import asyncio
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import tempfile
import zipfile

import getpass
from platformdirs import user_log_dir
import requests
from mcp.server.fastmcp import FastMCP
from typing import Annotated
from pydantic import Field

from . import __version__
from .extract_from_sqlite import extract_session, is_sqlite_file
from .search import find_log_path_with_marker

mcp = FastMCP("vise-logger")

# Configure logging
root_logger = logging.getLogger()
user_id = getpass.getuser()
if api_key := os.getenv("VISE_LOG_API_KEY"):
    user_id = api_key.split("_")[1]

# OTEL logging
if (
    os.getenv("OTEL_RESOURCE_ATTRIBUTES")
    and os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    and os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
):
    print(
        f"OTEL env vars set, enabling OTEL logging to {os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')}."
    )
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import Resource

    headers = {}
    if otel_headers := os.getenv("OTEL_EXPORTER_OTLP_HEADERS"):  # to satisfy mypy
        headers["Authorization"] = otel_headers
    exporter = OTLPLogExporter(
        endpoint=f"{os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')}/v1/logs",
        headers=headers,
    )
    resource = Resource.create(
        {"service.instance.id": user_id}
    )  # This reads OTEL_RESOURCE_ATTRIBUTES automatically!
    provider = LoggerProvider(resource=resource)
    provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    set_logger_provider(provider)
    otel_handler = LoggingHandler(level=logging.DEBUG, logger_provider=provider)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    # Alternatively, filter out urllib3 logs to prevent HTTP request noise
    # class Urllib3Filter(logging.Filter):
    #     def filter(self, record):
    #         return not record.name.startswith('urllib3')
    # otel_handler.addFilter(Urllib3Filter())
    root_logger.addHandler(otel_handler)

# file logging
log_dir = Path(user_log_dir("vise-logger", user_id))
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "mcp_server.log"
print(f"Logs are being written to: '{log_file}'")
file_handler = logging.FileHandler(log_file)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

# console logging
if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

root_logger.setLevel(logging.DEBUG)

async def _configure_log_dir_background(marker: str) -> None:
    """Background task for configure_log_dir."""
    logging.info("--- STARTING LOG DIRECTORY CONFIGURATION IN BACKGROUND---")

    find_result = await asyncio.to_thread(find_log_path_with_marker, marker)

    if find_result:
        _log_file_path, path_to_zip, _tool = find_result
        result_message = f"Log directory found and verified: {path_to_zip.parent}"
    else:
        result_message = "Could not find a verifiable log directory."
    logging.info(result_message)


@mcp.tool()
async def configure_log_dir() -> str:
    """
    Finds and verifies the log directory for the coding tool.
    This is a long-running operation and may take minutes to hours.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    marker = f"Starting at {timestamp} to search for the vise coding tool's log directory. This will be a long-running background task, result will be stored in `locations.json`."

    asyncio.create_task(_configure_log_dir_background(marker))
    return marker


def _create_zip_archive(
    zip_file_path_name: str, path_to_zip: Path, log_file_path: Path
) -> None:
    """Creates a zip archive from path_to_zip (either file or directory)."""
    with zipfile.ZipFile(zip_file_path_name, "w", zipfile.ZIP_DEFLATED) as zip_archive:
        if path_to_zip.is_dir():
            root_dir_in_zip = path_to_zip.name
            # Add the root directory to the archive
            zip_archive.writestr(f"{root_dir_in_zip}/", "")
            for item in path_to_zip.rglob("*"):
                if item.is_file():
                    # Skip rating_location.txt to avoid duplication
                    if item.name == "rating_location.txt":
                        continue
                    try:
                        with open(item, "r", encoding="utf-8", errors="ignore") as f:
                            log_content = f.read()
                        # will be necessary once filter_content() is not a nop: filtered_content = filter_content(log_content)
                        filtered_content = log_content
                        arcname = Path(root_dir_in_zip) / item.relative_to(path_to_zip)
                        zip_archive.writestr(str(arcname), filtered_content)
                    except IOError as e:
                        logging.error(f"Error reading file {item}: {e}")
            zip_archive.writestr(
                str(Path(root_dir_in_zip) / "rating_location.txt"), log_file_path.name
            )
        else:
            assert path_to_zip == log_file_path, (
                "If not dir, then zip target must be log file"
            )
            try:
                with open(path_to_zip, "r", encoding="utf-8", errors="ignore") as f:
                    log_content = f.read()
                # will be necessary once filter_content() is not a nop: filtered_content = filter_content(log_content)
                filtered_content = log_content
                zip_archive.writestr(path_to_zip.name, filtered_content)
            except IOError as e:
                logging.error(f"Error reading log file: {e}")
                return


async def _rate_and_upload_background(marker: str, stars: float, comment: str) -> None:
    """Background task for rate_and_upload."""
    logging.info("--- STARTING SESSION UPLOAD IN BACKGROUND ---")

    find_result = await asyncio.to_thread(find_log_path_with_marker, marker)

    if not find_result:
        error_message = "Could not find the log file with the session marker."
        logging.error(error_message)
        return

    log_file_path, path_to_zip, coding_tool = find_result

    api_key = os.environ.get("VISE_LOG_API_KEY")
    if not api_key:
        logging.error("VISE_LOG_API_KEY environment variable not set.")
        return

    try:
        # Use a temporary directory and create a zip file path inside it. This avoids
        # Windows permission issues with NamedTemporaryFile being open while writing.
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "session.zip"

            if (
                coding_tool == "cursor"
                or log_file_path.suffix == ".vscdb"
                or is_sqlite_file(log_file_path)
            ):
                with tempfile.TemporaryDirectory() as extract_dir:
                    extract_dir_path = Path(extract_dir)
                    session, vl_format = extract_session(log_file_path, marker)

                    if not session and not vl_format:
                        logging.warning(
                            f"Could not extract session from {log_file_path}. "
                            "Falling back to zipping the original file."
                        )
                        _create_zip_archive(str(zip_path), path_to_zip, log_file_path)
                    else:
                        session_file = extract_dir_path / "session.json"
                        with open(session_file, "w") as f:
                            json.dump(session, f, indent=2)

                        vl_format_file = extract_dir_path / "vl_format.json"
                        with open(vl_format_file, "w") as f:
                            json.dump(vl_format, f, indent=2)

                        _create_zip_archive(str(zip_path), extract_dir_path, session_file)
            else:
                _create_zip_archive(str(zip_path), path_to_zip, log_file_path)

            metadata = {
                "marker": marker,
                "tool": coding_tool,
                "stars": stars,
                "comment": comment,
            }

            with open(zip_path, "rb") as file_to_upload:
                headers = {"X-API-Key": api_key}
                files = {"file": ("session.zip", file_to_upload, "application/zip")}
                data = {"metadata": json.dumps(metadata)}

                response = requests.post(
                    "https://studio--viselog.us-central1.hosted.app/api/v1/sessions",
                    data=data,
                    files=files,
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()

            logging.info("Session successfully uploaded to server.")
            logging.info(f"Temporary file {str(zip_path)} removed.")

    except (IOError, requests.exceptions.RequestException, zipfile.BadZipFile) as e:
        error_message = f"Failed to create or upload session zip file: {e}"
        logging.error(error_message)


@mcp.tool()
async def rate_and_upload(  # Annotated as workaround since https://github.com/modelcontextprotocol/python-sdk/issues/226 is not yet fixed:
    stars: Annotated[
        float, Field(description="Stars between 1 and 5 rating the session", ge=1, le=5)
    ],
    comment: Annotated[
        str, Field(description="Optional comment about the rating or session")
    ] = "",
) -> str:
    """Upload and rate the current Vise Coding session.

    Args:
        stars: stars between 1 and 5 rating the session
        comment: optional comment about the rating or session
    """
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    marker = f"Rated session at {timestamp}: {stars} stars. Uploading session in the background."
    asyncio.create_task(_rate_and_upload_background(marker, stars, comment))
    return marker


def main() -> None:
    """Synchronous entry point."""
    logging.info("vise-logger %s", __version__)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
