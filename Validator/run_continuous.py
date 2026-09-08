"""Continuously run Validator one business opportunity at a time."""

import argparse
import time
import traceback

from config import VALIDATOR_CONTINUOUS_RUN_DURATION_SECONDS, get_database_path
from database import select_next_opportunity
from run_log import run_log
from validate_business import run_validator_iteration


def parse_args() -> argparse.Namespace:
    """Parse command-line options for the continuous runner."""
    parser = argparse.ArgumentParser(
        description="Keep Validator running by repeating one-opportunity runs."
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
    """Run Validator repeatedly until the configured duration or interruption."""
    args = parse_args()
    if args.interval < 0:
        raise ValueError("--interval must be zero or greater")
    if VALIDATOR_CONTINUOUS_RUN_DURATION_SECONDS < 0:
        raise ValueError(
            "VALIDATOR_CONTINUOUS_RUN_DURATION_SECONDS must be zero or greater"
        )

    duration = VALIDATOR_CONTINUOUS_RUN_DURATION_SECONDS
    deadline = time.monotonic() + duration if duration else None
    if deadline is None:
        print(f"Continuous Validator enabled; waiting {args.interval} seconds between runs.")
    else:
        print(
            f"Continuous Validator enabled for {duration} seconds; "
            f"waiting {args.interval} seconds between runs."
        )

    try:
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                print("Continuous run duration reached; stopping before the next iteration.")
                break

            iteration_failed = False
            with run_log("continuous"):
                try:
                    run_validator_iteration()
                except Exception as error:
                    iteration_failed = True
                    print(f"Validator iteration failed: {error}")
                    traceback.print_exc()

            if not iteration_failed and select_next_opportunity(get_database_path()) is None:
                print("No Validator opportunities remain; stopping continuous run.")
                break

            if deadline is not None and time.monotonic() >= deadline:
                print("Continuous run duration reached; stopping after the completed iteration.")
                break

            print(f"Waiting {args.interval} seconds before the next iteration...")
            wait_seconds = args.interval
            if deadline is not None:
                wait_seconds = min(wait_seconds, max(0, deadline - time.monotonic()))
            time.sleep(wait_seconds)
    except KeyboardInterrupt:
        print("\nContinuous Validator stopped.")


if __name__ == "__main__":
    main()