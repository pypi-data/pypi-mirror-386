import json
import logging
import os
import platform
from pathlib import Path
import time
from typing import Optional, List, Dict, Any, Tuple

MB = 1024 * 1024
MAX_FILE_SIZE = 10 * MB
MAX_DIR_SIZE = 50 * MB
MAX_SUFFIXES = 4
WAIT_FOR_TOOL_WRITING_SECONDS = 25

EXCLUDED_DIR_NAMES = {
    "node_modules",
    ".npm",
    ".yarn",
    ".pnpm",
    ".nuget",
    ".next",
    ".nuxt",
    "__pycache__",
    ".pytest_cache",
    "anaconda2",
    "anaconda3",
    "miniconda2",
    "miniconda3",
    ".cargo",
    ".rustup",
    ".gradle",
    ".m2",
    ".cache",
    "Cache",
    "Caches",
    ".pub-cache",
    ".parcel-cache",
    "Steam",
    "Games",
    "Epic Games",
    ".docker",
    "VirtualBox VMs",
    ".vagrant",
    "Movies",
    "Music",
    "Pictures",
    "Videos",
    ".mozilla",
    ".chromium",
    "snap",
}

EXCLUDED_PATH_SUFFIXES = {
    ".local/share/containers",
    "Documents/Adobe",
}

LOCATIONS_FILE = Path(__file__).parent / "locations.json"


def _read_locations() -> List[Dict[str, Any]]:
    """Reads log locations from the JSON file."""
    if not LOCATIONS_FILE.exists():
        return []
    with open(LOCATIONS_FILE, "r") as f:
        data: Dict[str, Any] = json.load(f)
        return data.get("locations", [])


def _save_locations_and_log(locations: List[Dict[str, Any]], dir_path: Path) -> None:
    """Persist locations.json and log a standardized update message.

    Args:
        locations: The list of location dicts to persist.
        dir_path: The directory path relevant to the update (used in log message).
    """
    with open(LOCATIONS_FILE, "w") as f:
        json.dump({"locations": locations}, f, indent=2)
    logging.info(f"Updated/Added verified log location: {dir_path}")


def _detect_log_directory(found_path: Path) -> Path:
    """
    Detects the log path (found_path or its parent directory) based on some criteria:
    1. if the directory contains only one file, return that file
    2. the size of the directory
    3. the number of files with the same suffix in the directory
    """
    directory = found_path.parent

    # sole file criterion
    if len(list(directory.iterdir())) == 1:
        assert found_path.is_file(), "Expected found_path to be a file"
        logging.debug(
            "Picking directory as log file is the only file in the directory."
        )
        return directory

    # directory size criterion
    try:
        size = sum(f.stat().st_size for f in directory.glob("**/*") if f.is_file())
        if size > MAX_DIR_SIZE:
            logging.debug(
                "Picking log file and not log dir as dir size exceeds limit: %s", size
            )
            return found_path
    except (IOError, OSError, FileNotFoundError):
        pass

    # suffix amount criterion
    suffix = found_path.suffix
    if suffix:
        try:
            files_with_same_suffix = [
                f for f in directory.iterdir() if f.suffix == suffix
            ]
            if len(files_with_same_suffix) > MAX_SUFFIXES:
                logging.debug(
                    "Picking log file and not log dir as too many files with the same suffix: %s",
                    len(files_with_same_suffix),
                )
                return found_path
        except (IOError, OSError, FileNotFoundError):
            pass
    return directory


def _add_location(path_to_zip: Path) -> str:
    """Adds or updates a location, with verified:true"""
    dir_of_all_logs = path_to_zip.parent
    locations = _read_locations()
    for loc in locations:
        if path_to_zip.is_relative_to(_expand_path(loc.get("dir", ""))):
            loc["verified"] = True
            logging.info(f"Updating existing location: {loc}")
            _save_locations_and_log(locations, dir_of_all_logs)
            return loc["tool"]

    logging.info(f"Adding new location: {str(dir_of_all_logs)}")
    locations.append({"dir": str(dir_of_all_logs), "tool": "unknown", "verified": True})
    _save_locations_and_log(locations, dir_of_all_logs)
    return "unknown"


def _expand_path(path_str: str) -> Path:
    """Expands environment variables and home directory tilde in a path string."""
    path_str = os.path.expanduser(path_str)

    if "%APPDATA%" in path_str:
        appdata = None
        if platform.system() == "Windows":
            appdata = os.getenv("APPDATA")
        elif platform.system() == "Linux":
            appdata = os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        elif platform.system() == "Darwin":
            appdata = str(Path.home() / "Library/Application Support")

        if appdata:
            path_str = path_str.replace("%APPDATA%", appdata)
        else:
            return Path(f"/non_existent_path_{os.urandom(8).hex()}")

    return Path(os.path.expandvars(path_str))


def _search_path(
    directory: Path,
    marker: str,
    paths_not_to_traverse_into: set = EXCLUDED_PATH_SUFFIXES,
) -> Optional[Path]:
    """Recursively searches a directory (outside of paths_not_to_traverse_into) for a file containing the marker.
    Returns the file path if found, otherwise None."""
    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = [
            d
            for d in dirs
            if d not in EXCLUDED_DIR_NAMES
            and not any(
                str(Path(root, d)).endswith(p) for p in paths_not_to_traverse_into
            )
        ]

        for file in files:
            file_path = Path(root) / file
            try:
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if marker in line:
                            logging.info("Marker found in: %s", file_path)
                            return file_path
            except (IOError, OSError, FileNotFoundError):
                continue
    return None


def _stage_1_and_2_search(marker: str) -> Optional[Tuple[Path, Path, str]]:
    locations = _read_locations()

    # Stage 1: Search in verified predefined locations
    logging.info("Stage 1: Searching in verified predefined locations.")
    for loc in [loc for loc in locations if loc.get("verified")]:
        expanded_path = _expand_path(loc.get("dir", ""))
        if expanded_path.exists() and expanded_path.is_dir():
            logging.info("Stage 1: Trying expanded_path %s", expanded_path)
            found_path = _search_path(expanded_path, marker)
            if found_path:
                return (
                    found_path,
                    _detect_log_directory(found_path),
                    loc.get("tool", "unknown"),
                )

    # Stage 2: Search in unverified predefined locations
    logging.info("Stage 2: Searching in unverified predefined locations.")
    for loc in [loc for loc in locations if not loc.get("verified")]:
        expanded_path = _expand_path(loc["dir"])
        if expanded_path.exists() and expanded_path.is_dir():
            logging.info("Stage 2: Trying expanded_path %s", expanded_path)
            found_path = _search_path(expanded_path, marker)
            if found_path:
                loc["verified"] = True
                _save_locations_and_log(locations, loc["dir"])
                return (
                    found_path,
                    _detect_log_directory(found_path),
                    loc.get("tool", "unknown"),
                )

    return None


def find_log_path_with_marker(marker: str) -> Optional[Tuple[Path, Path, str]]:
    """
    Finds the log file containing the unique marker by searching in a prioritized order,
    or the directory where the log file is located in case that whole directory represents the log/session.

    returns:
        A tuple of the found log file path, the path to zip, and the tool name; or None if not found
    """
    logging.info("Searching for log file with marker")

    # Stage 1 and 2 with "exponential" backoff
    result = _stage_1_and_2_search(marker)
    if result:
        return result
    logging.info(
        f"Backing off for {WAIT_FOR_TOOL_WRITING_SECONDS} seconds because some tools take time to write their logs"
    )
    time.sleep(WAIT_FOR_TOOL_WRITING_SECONDS)
    result = _stage_1_and_2_search(marker)
    if result:
        return result

    # Stage 3: Search in home directory
    logging.info("Stage 3: Searching in home directory.")
    home_dir = Path.home()
    found_path = _search_path(home_dir, marker)
    if found_path:
        path_to_zip = _detect_log_directory(found_path)
        tool = _add_location(path_to_zip)
        return found_path, path_to_zip, tool

    # Stage 4: Search the rest of the hard drive
    logging.info(
        "Stage 4: Searching the rest of the hard drive. This may take a while."
    )
    drives = [Path("/")]
    if platform.system() == "Windows":
        drives.extend(
            [
                Path(f"{chr(drive)}:\\")
                for drive in range(ord("A"), ord("Z") + 1)
                if Path(f"{chr(drive)}:\\").exists()
            ]
        )

    paths_not_to_traverse_into = EXCLUDED_PATH_SUFFIXES.union({str(home_dir)})
    for drive in drives:
        try:
            found_path = _search_path(drive, marker, paths_not_to_traverse_into)
            if found_path:
                path_to_zip = _detect_log_directory(found_path)
                tool = _add_location(path_to_zip)
                return found_path, path_to_zip, tool
        except PermissionError:
            continue

    logging.error("Log file with marker not found.")
    return None
