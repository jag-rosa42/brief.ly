"""Download and verify the pinned Ubuntu cloud image."""

import hashlib
import os
import sys
import urllib.request

image_path, image_url, checksum_url, image_name = sys.argv[1:]
print(f"Fetching Ubuntu checksum list: {checksum_url}", flush=True)
with urllib.request.urlopen(checksum_url, timeout=60) as response:
    checksum_lines = response.read().decode("ascii").splitlines()
expected = None
for line in checksum_lines:
    fields = line.split()
    if len(fields) == 2 and fields[1].lstrip("*") == image_name:
        expected = fields[0].lower()
        break
if expected is None:
    raise SystemExit(f"No SHA-256 checksum for {image_name} in {checksum_url}")

def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

if os.path.exists(image_path):
    actual = sha256_file(image_path)
    if actual != expected:
        raise SystemExit(f"Cached Ubuntu image checksum mismatch: {image_path}")
    print(f"Using verified cached image: {image_path}", flush=True)
    raise SystemExit(0)

partial_path = image_path + ".part"
try:
    print(f"Downloading Ubuntu cloud image: {image_url}", flush=True)
    with urllib.request.urlopen(image_url, timeout=60) as response, open(partial_path, "wb") as image:
        total = int(response.headers.get("Content-Length", "0"))
        downloaded = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            image.write(chunk)
            downloaded += len(chunk)
            if total:
                print(f"\rDownloaded {downloaded / (1024 ** 2):.0f} / {total / (1024 ** 2):.0f} MiB", end="", flush=True)
    if total:
        print(flush=True)
    actual = sha256_file(partial_path)
    if actual != expected:
        raise RuntimeError(f"SHA-256 verification failed: expected {expected}, got {actual}")
    os.replace(partial_path, image_path)
    print(f"Verified and cached cloud image: {image_path}", flush=True)
except Exception:
    try:
        os.remove(partial_path)
    except FileNotFoundError:
        pass
    raise
