"""Continuously run the Scout application one iteration at a time."""

import argparse
import time
import traceback

from config import config
from run_log import run_log
from scout import ScoutApp


def parse_args() -> argparse.Namespace:
    """Parse command-line options for the continuous runner."""
    parser = argparse.ArgumentParser(
        description="Keep Scout running by repeating its one-iteration run loop."
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        metavar="SECONDS",
        help="Seconds to wait between iterations (default: 30).",
    )
    return parser.parse_args()


def main() -> None:
    """Run Scout repeatedly until interrupted."""
    args = parse_args()
    if args.interval < 0:
        raise ValueError("--interval must be zero or greater")

    duration = config['continuous_run_duration_seconds']
    if duration < 0:
        raise ValueError("SCOUT_CONTINUOUS_RUN_DURATION_SECONDS must be zero or greater")

    deadline = time.monotonic() + duration if duration else None
    if deadline is None:
        print(f"Continuous mode enabled; waiting {args.interval} seconds between runs.")
    else:
        print(
            f"Continuous mode enabled for {duration} seconds; "
            f"waiting {args.interval} seconds between runs."
        )

    try:
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                print("Continuous run duration reached; stopping before the next iteration.")
                break

            with run_log("continuous"):
                try:
                    if 'app' not in locals():
                        app = ScoutApp()
                    app.run()
                except Exception as error:
                    print(f"Scout iteration failed: {error}")
                    traceback.print_exc()

            if deadline is not None and time.monotonic() >= deadline:
                print("Continuous run duration reached; stopping after the completed iteration.")
                break

            print(f"Waiting {args.interval} seconds before the next iteration...")
            wait_seconds = args.interval
            if deadline is not None:
                wait_seconds = min(wait_seconds, max(0, deadline - time.monotonic()))
            time.sleep(wait_seconds)
    except KeyboardInterrupt:
        print("\nContinuous Scout stopped.")


if __name__ == "__main__":
    main()
