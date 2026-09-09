"""Per-run console and file logging for Phase 4."""

from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
import sys
from typing import Iterator, TextIO


class _Tee:
    def __init__(self, terminal: TextIO, log_file: TextIO) -> None:
        self.terminal = terminal
        self.log_file = log_file

    def write(self, text: str) -> int:
        self.terminal.write(text)
        self.log_file.write(text)
        self.log_file.flush()
        return len(text)

    def flush(self) -> None:
        self.terminal.flush()
        self.log_file.flush()

    def isatty(self) -> bool:
        return self.terminal.isatty()

    def fileno(self) -> int:
        return self.terminal.fileno()


@contextmanager
def run_log(mode: str) -> Iterator[Path]:
    logs_dir = Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_path = logs_dir / f"definition_{timestamp}.log"
    with log_path.open("w", encoding="utf-8") as log_file:
        with redirect_stdout(_Tee(sys.stdout, log_file)), redirect_stderr(_Tee(sys.stderr, log_file)):
            print(f"Run started: {datetime.now().isoformat(timespec='seconds')}")
            print(f"Run mode: {mode}")
            print(f"Log file: {log_path}")
            try:
                yield log_path
            finally:
                print(f"Run ended: {datetime.now().isoformat(timespec='seconds')}")


__all__ = ["run_log"]
