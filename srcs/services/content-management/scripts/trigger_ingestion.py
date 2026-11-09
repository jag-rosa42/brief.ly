"""Trigger Content Management ingestion through its internal HTTP endpoint."""

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener

INGESTION_PATH = "/internal/v1/ingestion-runs"
DEFAULT_TIMEOUT = 600


class TriggerError(Exception):
    """A failure that should be reported to the script caller."""


def _error_message(body: bytes) -> str:
    try:
        payload = json.loads(body)
    except UnicodeDecodeError, json.JSONDecodeError:
        return body.decode(encoding="utf-8", errors="replace").strip()

    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            code = error.get("code")
            message = error.get("message")
            if isinstance(code, str) and isinstance(message, str):
                return f"{code}: {message}"
    return body.decode(encoding="utf-8", errors="replace").strip()


def _validate_secret_file(secret_file: Path) -> None:
    if not secret_file.is_file():
        raise TriggerError(f"NewsAPI key file is missing: {secret_file}")
    try:
        if not secret_file.read_bytes().strip():
            raise TriggerError(f"NewsAPI key file is empty: {secret_file}")
    except OSError as exc:
        raise TriggerError(
            f"Cannot read NewsAPI key file {secret_file}: {exc.strerror}"
        ) from exc


def _ingestion_endpoint(url: str) -> str:
    try:
        parsed = urlparse(url)
        _ = parsed.port  # Also validate a supplied port.
    except ValueError:
        parsed = None
    if (
        parsed is None
        or parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.query
        or parsed.fragment
    ):
        raise TriggerError(f"Invalid Content Management URL: {url}")
    return url.rstrip("/") + INGESTION_PATH


def _send_ingestion_request(endpoint: str, timeout: float) -> tuple[int, bytes]:
    request = Request(url=endpoint, method="POST", headers={"Accept": "application/json"})
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(fullurl=request, timeout=timeout) as response:
            return response.status, response.read()
    except HTTPError as exc:
        raise TriggerError(
            f"Ingestion failed (HTTP {exc.code}): {_error_message(body=exc.read())}"
        ) from exc
    except (OSError, URLError) as exc:
        raise TriggerError(
            f"Cannot reach Content Management at {endpoint}: {exc}"
        ) from exc


def _parse_ingestion_result(status_code: int, body: bytes) -> str:
    if status_code != 201:
        raise TriggerError(
            f"Unexpected ingestion response (HTTP {status_code}): {_error_message(body)}"
        )
    try:
        payload = json.loads(body)
    except UnicodeDecodeError, json.JSONDecodeError:
        raise TriggerError("Invalid ingestion response: expected JSON.") from None
    if not isinstance(payload, dict):
        raise TriggerError("Invalid ingestion response: expected a status object.")
    status = payload.get("status")
    if status in ("succeeded", "partial"):
        return status
    raise TriggerError(f"Invalid ingestion status: {status!r}")


def trigger(url: str, secret_file: Path, timeout: float = DEFAULT_TIMEOUT) -> int:
    try:
        _validate_secret_file(secret_file)
        endpoint: str = _ingestion_endpoint(url)
        status_code: int
        body: bytes
        status_code, body = _send_ingestion_request(endpoint, timeout)
        status: str = _parse_ingestion_result(status_code, body)
    except TriggerError as exc:
        print(exc, file=sys.stderr)
        return 1

    if status == "succeeded":
        print("Ingestion succeeded.")
    else:
        print(
            "Ingestion partially succeeded; check Content Management logs for failures.",
            file=sys.stderr,
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Content Management base URL")
    parser.add_argument("--secret-file", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error(message="--timeout must be greater than zero")
    return trigger(args.url, args.secret_file, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
