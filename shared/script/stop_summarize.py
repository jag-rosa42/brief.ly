"""Run inside the AI Processing container to stop manually launched workers."""

import os
import signal
import time
from pathlib import Path


def is_worker(process: Path) -> bool:
    try:
        command = (process / "cmdline").read_bytes().rstrip(b"\0").split(b"\0")
    except FileNotFoundError:
        return False
    return (
        len(command) == 3
        and Path(os.fsdecode(command[0])).name.startswith("python")
        and command[1:] == [b"-m", b"src.worker"]
    )


def main() -> int:
    workers = [p for p in Path("/proc").glob("[0-9]*") if is_worker(p)]
    if not workers:
        print("[AI PROCESSING] No summary worker is running.")
        return 0

    for process in workers:
        try:
            os.kill(int(process.name), signal.SIGTERM)
        except ProcessLookupError:
            pass

    # SIGTERM interrupts in-flight HTTP calls. Completed database writes stay saved.
    deadline = time.monotonic() + 5
    while any(is_worker(p) for p in workers):
        if time.monotonic() >= deadline:
            print("[AI PROCESSING] Workers did not stop within 5 seconds.", flush=True)
            return 1
        time.sleep(0.1)

    print(f"[AI PROCESSING] Stopped {len(workers)} summary worker(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
