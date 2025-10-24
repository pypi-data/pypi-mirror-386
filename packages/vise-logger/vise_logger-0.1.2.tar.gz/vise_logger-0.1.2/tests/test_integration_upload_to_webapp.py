import unittest
import io
import zipfile
import json
import os
import requests
from datetime import datetime


class TestWebAppUpload(unittest.TestCase):
    def test_upload_session_to_webapp(self) -> None:
        """
        Tests the successful upload of a session to the web application's POST endpoint.
        """
        # Create an in-memory zip file
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        stars = 1.0
        marker = f"Rated session at {timestamp}: {stars} stars. Uploading session in the background."
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("test_session/", "")  # Create a directory
            zip_file.writestr("test_session/session.foo", marker)
        zip_buffer.seek(0)

        # Prepare metadata
        metadata = {
            "marker": marker,
            "tool": "test_tool",
            "stars": stars,
            "comment": "This is a test comment.",
        }

        api_key = os.environ.get("VISE_LOG_API_KEY")
        if not api_key:
            self.fail("VISE_LOG_API_KEY environment variable not set.")

        headers = {"X-API-Key": api_key}
        files = {"file": ("session.zip", zip_buffer, "application/zip")}
        data = {"metadata": json.dumps(metadata)}

        try:
            response = requests.post(
                "https://studio--viselog.us-central1.hosted.app/api/v1/sessions",
                data=data,
                files=files,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            self.assertEqual(response.status_code, 200)
            print(
                f"Successfully uploaded test session. Server response: {response.text}"
            )

        except requests.exceptions.RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                self.fail(
                    f"Failed to upload session to webapp: {e}\nResponse: {e.response.text}"
                )
            else:
                self.fail(f"Failed to upload session to webapp: {e}")


if __name__ == "__main__":
    unittest.main()
