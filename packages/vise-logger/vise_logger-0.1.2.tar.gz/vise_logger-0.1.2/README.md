# Vise Logger

Vise Logger is an MCP server that captures, rates, and archives Vise Coding sessions from various AI coding tools (Cursor, GitHub Copilot, Cline, ...), storing them at viselo.gr for reference, comparisons, and searchability.

As Sean Grove (OpenAI) and Dexter Horthy (HumanLayer) say: **The source spec (i.e. coding sessions) is the most valuable artifact**.

Just like you used to store the source code, not binaries, in GitHub,
you should now store your coding sessions as main source of truth, and not throw them away upon ending the coding session.

On viselo.gr, you have
* an overview of your sessions
* a backup, as you can download each session as zip, containing the original format
* can share sessions with others
* get insights and advise from your sessions and of shared sessions.

Features planned for the future: further advise, search, and statistics (see https://fb-swt.gi.de/fileadmin/FB/SWT/Softwaretechnik-Trends/Verzeichnis/Band_45_Heft_3/5_TAV51_Farago.pdf).


## Installation and Setup

### Local installation

This project uses `uv` for package and environment management.

1.  **Create a virtual environment:**
    ```bash
    uv venv
    ```

2.  **Activate the virtual environment:**
    *   On macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```
    *   On Windows:
        ```bash
        .venv\Scripts\activate
        ```

3.  **Install the project in editable mode:**
    This command installs the project and its dependencies into the virtual environment. The `-e` flag (editable) ensures that any changes you make to the source code are immediately available without needing to reinstall.
    ```bash
    uv sync --extra dev
    ```
    This installs the runtime and dev dependencies, in editable mode. To only install the runtime dependencies, leave out argument `--extra dev`

4.  **Quality gates:**
    Formatting: `uv run ruff format . && uv run ruff check .`
    Type checking: `uv run mypy .`
    Testing: `VISE_LOG_API_KEY=you_API_key_from_viselo.gr uv run pytest`


### Installation of MCP Server via PyPI

### Making use of the MCP server in your AI coding tool

Locally installed (example from Cline / Roo / Kilo):
```json
"vise-logger": {
  "disabled": false,
  "timeout": 60,
  "type": "stdio",
  "command": "uv",
  "args": [
    "--directory",
    "/home/emergency/git/vise-logger",
    "run",
    "vise-logger"
  ],
  "env": {
    "VISE_LOG_API_KEY": "your_API_key_from_viselo.gr",
    "OTEL_RESOURCE_ATTRIBUTES": "service.name=vise-logger,service.namespace=public-logs,deployment.environment=production",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otlp-gateway-prod-eu-west-2.grafana.net/otlp",
    "OTEL_EXPORTER_OTLP_HEADERS": "Basic MTM2MjQxMTpnbGNfZXlKdklqb2lNVFV5TWpJM05pSXNJbTRpT2lKMmFYTmxMV3h2WjJkbGNpSXNJbXNpT2lKMGNtd3ljRGM1U0ZCU1ZWQjNORGRrZEV3M05EUTNORTRpTENKdElqcDdJbklpT2lKd2NtOWtMV1YxTFhkbGMzUXRNaUo5ZlE9PQ=="
  }
}
```

Installed (with anonymization) through PyPI by adding the following to the MCP config file:
```json
"vise-logger": {
  "disabled": false,
  "timeout": 60,
  "type": "stdio",
  "command": "uv",
  "args": ["tool", "run", "vise-logger"],
  "env": {
    "PSEUDONYMIZATION_ENCRYPTION_KEY": "key via openssl rand -base64 32",
    "VISE_LOG_API_KEY": "your_API_key_from_viselo.gr",
    "OTEL_RESOURCE_ATTRIBUTES": "service.name=vise-logger,service.namespace=public-logs,deployment.environment=production",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otlp-gateway-prod-eu-west-2.grafana.net/otlp",
    "OTEL_EXPORTER_OTLP_HEADERS": "Basic MTM2MjQxMTpnbGNfZXlKdklqb2lNVFV5TWpJM05pSXNJbTRpT2lKMmFYTmxMV3h2WjJkbGNpSXNJbXNpT2lKMGNtd3ljRGM1U0ZCU1ZWQjNORGRrZEV3M05EUTNORTRpTENKdElqcDdJbklpT2lKd2NtOWtMV1YxTFhkbGMzUXRNaUo5ZlE9PQ=="
  }
}
```

In VS Code, you can also do the installation (with anonymization) through the following command line:
```bash
code --add-mcp '{"name":"vise-logger","disabled":false,"timeout":60,"type":"stdio","command":"uv","args":["tool","run","vise-logger"],"env":{"PSEUDONYMIZATION_ENCRYPTION_KEY":"key via openssl rand -base64 32","VISE_LOG_API_KEY":"your_API_key_from_viselo.gr","OTEL_RESOURCE_ATTRIBUTES":"service.name=vise-logger,service.namespace=public-logs,deployment.environment=production","OTEL_EXPORTER_OTLP_ENDPOINT":"https://otlp-gateway-prod-eu-west-2.grafana.net/otlp","OTEL_EXPORTER_OTLP_HEADERS":"Basic MTM2MjQxMTpnbGNfZXlKdklqb2lNVFV5TWpJM05pSXNJbTRpT2lKMmFYTmxMV3h2WjJkbGNpSXNJbXNpT2lKMGNtd3ljRGM1U0ZCU1ZWQjNORGRrZEV3M05EUTNORTRpTENKdElqcDdJbklpT2lKd2NtOWtMV1YxTFhkbGMzUXRNaUo5ZlE9PQ=="}}'
```


## Environment Variables

`VISE_LOG_API_KEY`: Required. The API key for authenticating with the Vise Logger backend. This key is necessary for uploading sessions. Get it at https://viselo.gr/ by signing in, going to settings and then "Generate New Key".
The key is only shown once, so make sure you save it.

`OTEL_RESOURCE_ATTRIBUTES` (default "service.name=vise-logger,service.namespace=public-logs,deployment.environment=production"), `OTEL_EXPORTER_OTLP_ENDPOINT` (default "https://otlp-gateway-prod-eu-west-2.grafana.net/otlp"), and `OTEL_EXPORTER_OTLP_HEADERS` (default "Basic MTM2MjQxMTpnbGNfZXlKdklqb2lNVFV5TWpJM05pSXNJbTRpT2lKMmFYTmxMV3h2WjJkbGNpSXNJbXNpT2lKMGNtd3ljRGM1U0ZCU1ZWQjNORGRrZEV3M05EUTNORTRpTENKdElqcDdJbklpT2lKd2NtOWtMV1YxTFhkbGMzUXRNaUo5ZlE9PQ=="): Optional. The logs are sent to the MCP host and to a file (see below), but you can also use open telemetry to send your logs to a server with an open telemetry endpoint. If you use the default values, they are sent to the developer of this project.


## Running the MCP Server

To run the MCP server directly from the command line:

```bash
vise-logger
```

## MCP Tools

This server provides two tools:

### `rate_and_upload(stars: float, comment: str = "")`

Rates and archives the current Vise Coding session. It finds the relevant log file, filters it for privacy, and simulates an upload to the backend.

### `configure_log_dir()`

Scans the system to find and verify the directory where your coding tool saves its logs. This helps speed up future searches.

**Warning:** This can be a very long-running operation, potentially taking minutes to hours, as it may scan your entire hard drive.

## Running Tests

With the virtual environment activated and the project installed in editable mode, you can run the integration tests:

```bash
python3 -m unittest discover tests
```

**Note on Best Practices:** Installing the package in editable mode (`-e`) is the recommended way to run tests for a distributable Python package. It correctly resolves imports without needing to modify `sys.path`, which is a less robust method. This approach simulates a real installation, making the testing environment more realistic.

## REST Endpoints The Sessions Are Sent to

The endpoint should have Content-Type: multipart/form-data and the following form fields:
* file (required): The zip file containing the AI coding session data
* metadata (required): JSON string with AI coding session metadata. The metadata JSON structure:
```
json{
  "marker": "string (required)",
  "tool": "string (required)",
  "stars": "number (required)",
  "comment": "string (optional)"
}
```

The official web application for Vise Logger is www.viselo.gr.
You can test it via
```
curl -X POST \
  -F "file=@session.zip" \
  -F 'metadata={"marker": "Rated session at 2025-07-30-20-56-11: 1.9 stars.", "tool": "curl", "stars": 1.9, "comment": "Just a curl test"}' \
  "https://studio--viselog.us-central1.hosted.app/api/v1/sessions"
```

## MCP server's logging and debugging

MCP-Server's own logs: if environment variables OTEL_RESOURCE_ATTRIBUTES, OTEL_EXPORTER_OTLP_ENDPOINT, and OTEL_EXPORTER_OTLP_HEADERS are set,
open telemetry (http/protobuf) is used for logging. You can log to the developer's cloud instance using
```
OTEL_RESOURCE_ATTRIBUTES="service.name=vise-logger,service.namespace=public-logs,deployment.environment=production"
OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp-gateway-prod-eu-west-2.grafana.net/otlp"
OTEL_EXPORTER_OTLP_HEADERS="Basic MTM2MjQxMTpnbGNfZXlKdklqb2lNVFV5TWpJM05pSXNJbTRpT2lKMmFYTmxMV3h2WjJkbGNpSXNJbXNpT2lKMGNtd3ljRGM1U0ZCU1ZWQjNORGRrZEV3M05EUTNORTRpTENKdElqcDdJbklpT2lKd2NtOWtMV1YxTFhkbGMzUXRNaUo5ZlE9PQ=="
```
Logs are also written to a file, e.g. 
 `~/.local/state/vise-logger/log/mcp_server.log` 
 (path depends on your machine, see https://pypi.org/project/platformdirs/).
