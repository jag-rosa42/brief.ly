import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from scripts.trigger_ingestion import trigger


class TriggerIngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.secret_file = Path(self.temp_dir.name) / "news_api_key"
        self.secret_file.write_text("test-key")
        self.output = io.StringIO()
        self.errors = io.StringIO()

    def _run(self, response=None, failure=None) -> int:
        opener = MagicMock()
        if failure is not None:
            opener.open.side_effect = failure
        else:
            opener.open.return_value.__enter__.return_value = response
        with (
            patch("scripts.trigger_ingestion.build_opener", return_value=opener),
            redirect_stdout(self.output),
            redirect_stderr(self.errors),
        ):
            return trigger("http://127.0.0.1:8000", self.secret_file)

    def test_success(self) -> None:
        response = MagicMock(status=201)
        response.read.return_value = b'{"status":"succeeded"}'
        self.assertEqual(self._run(response=response), 0)
        self.assertIn("Ingestion succeeded", self.output.getvalue())

    def test_partial_result_is_visible(self) -> None:
        response = MagicMock(status=201)
        response.read.return_value = b'{"status":"partial"}'
        self.assertEqual(self._run(response=response), 0)
        self.assertIn("partially succeeded", self.errors.getvalue())

    def test_http_error_reports_status_and_api_message(self) -> None:
        failure = HTTPError(
            "http://127.0.0.1:8000/internal/v1/ingestion-runs",
            502,
            "Bad Gateway",
            Message(),
            io.BytesIO(
                b'{"error":{"code":"INGESTION_FAILED","message":"No articles stored."}}'
            ),
        )
        self.assertEqual(self._run(failure=failure), 1)
        self.assertIn("HTTP 502", self.errors.getvalue())
        self.assertIn("INGESTION_FAILED: No articles stored.", self.errors.getvalue())

    def test_connection_error_is_actionable(self) -> None:
        self.assertEqual(self._run(failure=URLError("connection refused")), 1)
        self.assertIn("Cannot reach Content Management", self.errors.getvalue())

    def test_empty_secret_stops_before_request(self) -> None:
        self.secret_file.write_text("")
        self.assertEqual(self._run(), 1)
        self.assertIn("NewsAPI key file is empty", self.errors.getvalue())


if __name__ == "__main__":
    unittest.main()
