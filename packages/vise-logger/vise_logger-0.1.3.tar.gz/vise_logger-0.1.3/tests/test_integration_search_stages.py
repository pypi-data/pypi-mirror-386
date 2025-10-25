import json
from pathlib import Path
import uuid
import unittest

from vise_logger.search import (
    find_log_path_with_marker,
    LOCATIONS_FILE,
    _read_locations,
)


class TestSearchStages(unittest.TestCase):
    def test_stage1_predefined_location(self) -> None:
        """Test finding a log file in a predefined location."""
        marker = "Rated session at 2025-07-27-11-11-59: 4.7 stars. Now uploading session to server."
        # This file is expected to exist in the test environment
        expected_parent_dir = (
            Path.home()
            / ".config/Code/User/globalStorage/saoudrizwan.claude-dev/tasks/"
        )

        found_result = find_log_path_with_marker(marker)

        self.assertIsNotNone(found_result)
        assert found_result is not None
        found_log_path, found_path_to_zip, tool = found_result
        assert found_path_to_zip is not None
        self.assertEqual(found_log_path.parent, found_path_to_zip)
        self.assertEqual(found_path_to_zip.parent, expected_parent_dir)
        self.assertEqual(tool, "cline")

    def test_stage2_home_directory(self) -> None:
        """Test finding a log file in the home directory."""
        logs_dir = Path.home() / f"test_logs_{uuid.uuid4()}"
        logs_dir.mkdir(exist_ok=True)
        test_dir = logs_dir / f"test_vise_logger_{uuid.uuid4()}"
        test_dir.mkdir(exist_ok=True)
        log_file = test_dir / "test.log"
        marker = f"unique_marker_stage2_{uuid.uuid4()}"
        with open(log_file, "w") as f:
            f.write(marker)

        try:
            found_result = find_log_path_with_marker(marker)

            self.assertIsNotNone(found_result)
            assert found_result is not None
            found_log_path, found_path_to_zip, tool = found_result
            self.assertEqual(found_log_path, log_file)
            self.assertEqual(
                found_path_to_zip, log_file.parent
            )  # as only 1 file in directory
            self.assertEqual(tool, "unknown")
            locations = _read_locations()
            assert locations is not None, "Locations should not be None"
            assert locations != [], "Locations should not be empty"
            loc = next((loc for loc in locations if loc["dir"] == str(logs_dir)), None)
            assert loc is not None, (
                f"Location {logs_dir} should be found in locations.json"
            )
        finally:  # Cleanup
            if log_file.exists():
                log_file.unlink()
            if test_dir.exists():
                test_dir.rmdir()
            if locations and loc:
                locations.remove(loc)
                with open(LOCATIONS_FILE, "w") as f:
                    json.dump({"locations": locations}, f, indent=2)


if __name__ == "__main__":
    unittest.main()
