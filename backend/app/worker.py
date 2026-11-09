"""Supervised persistent C++ search worker."""
import os
import select
import subprocess
import threading
from pathlib import Path


class WorkerError(RuntimeError):
    pass


class SearchWorker:
    def __init__(self, binary: Path, corpus: list[Path]):
        self.binary = binary
        self.corpus = corpus
        self.lock = threading.Lock()
        self.process = None

    def _start(self):
        if self.process and self.process.poll() is None:
            return
        self.process = subprocess.Popen(
            [str(self.binary), *(str(path) for path in self.corpus)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=False, bufsize=0, close_fds=True,
        )

    def command(self, payload: str, timeout: float = 10) -> list[str]:
        with self.lock:
            self._start()
            try:
                self.process.stdin.write((payload + "\n").encode("ascii"))
                ready, _, _ = select.select([self.process.stdout], [], [], timeout)
                if not ready:
                    self.close()
                    raise WorkerError("Search worker timed out.")
                raw = self.process.stdout.readline()
                if not raw:
                    self.close()
                    raise WorkerError("Search worker stopped unexpectedly.")
                fields = raw.decode("ascii").rstrip("\n").split("\t")
                if fields[0] == "ERROR":
                    raise WorkerError(fields[1] if len(fields) > 1 else "Search worker rejected command.")
                return fields
            except (BrokenPipeError, OSError) as exc:
                self.close()
                raise WorkerError("Search worker unavailable.") from exc

    def scan(self, pattern: str, offset: int, limit: int, timeout_ms: int = 5000) -> dict:
        fields = self.command(f"SCAN\t{pattern}\t{offset}\t{limit}\t{timeout_ms}", timeout_ms / 1000 + 3)
        if len(fields) != 6 or fields[0] != "SCAN":
            raise WorkerError("Invalid worker response.")
        return {
            "complete": fields[1] == "1", "observed_count": int(fields[2]),
            "first_position": int(fields[3]) or None, "elapsed_ms": int(fields[4]),
            "matches": [int(item) for item in fields[5].split(",") if item],
        }

    def digits(self, start: int, count: int) -> str:
        fields = self.command(f"DIGITS\t{start}\t{count}")
        if len(fields) != 2 or fields[0] != "DIGITS":
            raise WorkerError("Invalid worker response.")
        return fields[1]

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        self.process = None
