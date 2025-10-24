import json
from pathlib import Path
from vise_logger.extract_from_sqlite import extract_session


def test_extract_session() -> None:
    """
    Tests that extract_session returns the correct session and vl_format data.
    """
    db_path = Path("tests/cursor_state.vscdb")
    marker = "Rated session at 2025-09-11-11-18-21: 4.6 stars. Uploading session in the background."
    expected_session_path = Path("tests/cursor_session.json")
    with open(expected_session_path, "r") as f:
        expected_session = json.load(f)
    expected_vl_format_path = Path("tests/cursor_vl_format.json")
    with open(expected_vl_format_path, "r") as f:
        expected_vl_format = json.load(f)

    session, vl_format = extract_session(db_path, marker)

    assert session == expected_session
    assert vl_format == expected_vl_format
