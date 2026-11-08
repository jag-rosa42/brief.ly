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


def _error_message(body: bytes) -> str:
    try:
        payload = json.loads(body)
    except UnicodeDecodeError, json.JSONDecodeError:
        return body.decode("utf-8", errors="replace").strip()

    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            code = error.get("code")
            message = error.get("message")
            if isinstance(code, str) and isinstance(message, str):
                return f"{code}: {message}"
    return body.decode("utf-8", errors="replace").strip()


def trigger(url: str, secret_file: Path, timeout: float = DEFAULT_TIMEOUT) -> int:
    if not secret_file.is_file():
        print(f"NewsAPI key file is missing: {secret_file}", file=sys.stderr)
        return 1
    try:
        if not secret_file.read_bytes().strip():
            print(f"NewsAPI key file is empty: {secret_file}", file=sys.stderr)
            return 1
    except OSError as exc:
        print(
            f"Cannot read NewsAPI key file {secret_file}: {exc.strerror}",
            file=sys.stderr,
        )
        return 1

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
        print(f"Invalid Content Management URL: {url}", file=sys.stderr)
        return 1
    endpoint = url.rstrip("/") + INGESTION_PATH
    request = Request(endpoint, method="POST", headers={"Accept": "application/json"})
    opener = build_opener(ProxyHandler({}))

    try:
        with opener.open(request, timeout=timeout) as response:
            status_code = response.status
            body = response.read()
    except HTTPError as exc:
        print(
            f"Ingestion failed (HTTP {exc.code}): {_error_message(exc.read())}",
            file=sys.stderr,
        )
        return 1
    except (OSError, URLError) as exc:
        print(f"Cannot reach Content Management at {endpoint}: {exc}", file=sys.stderr)
        return 1

    if status_code != 201:
        print(
            f"Unexpected ingestion response (HTTP {status_code}): {_error_message(body)}",
            file=sys.stderr,
        )
        return 1
    try:
        payload = json.loads(body)
    except UnicodeDecodeError, json.JSONDecodeError:
        print("Invalid ingestion response: expected JSON.", file=sys.stderr)
        return 1
    if not isinstance(payload, dict):
        print("Invalid ingestion response: expected a status object.", file=sys.stderr)
        return 1
    status = payload.get("status")
    if status == "succeeded":
        print("Ingestion succeeded.")
        return 0
    if status == "partial":
        print(
            "Ingestion partially succeeded; check Content Management logs for failures.",
            file=sys.stderr,
        )
        return 0
    print(f"Invalid ingestion status: {status!r}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Content Management base URL")
    parser.add_argument("--secret-file", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    return trigger(args.url, args.secret_file, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
