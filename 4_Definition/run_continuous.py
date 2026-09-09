"""Continuously define one product at a time."""

import argparse
import time
import traceback

try:
    from .config import PRODUCT_DEFINITION_CONTINUOUS_RUN_DURATION_SECONDS, get_database_path
    from .database import select_next_opportunity
    from .design_product import run_definition_iteration
    from .run_log import run_log
except ImportError:
    from config import PRODUCT_DEFINITION_CONTINUOUS_RUN_DURATION_SECONDS, get_database_path
    from database import select_next_opportunity
    from design_product import run_definition_iteration
    from run_log import run_log


def main() -> None:
    parser = argparse.ArgumentParser(description="Continuously define products one at a time.")
    parser.add_argument("--interval", type=int, default=30, metavar="SECONDS")
    args = parser.parse_args()
    if args.interval < 0 or PRODUCT_DEFINITION_CONTINUOUS_RUN_DURATION_SECONDS < 0:
        raise ValueError("interval and PRODUCT_DEFINITION_CONTINUOUS_RUN_DURATION_SECONDS must be zero or greater")
    duration = PRODUCT_DEFINITION_CONTINUOUS_RUN_DURATION_SECONDS
    deadline = time.monotonic() + duration if duration else None
    print("Continuous Definition enabled{}; waiting {} seconds between runs.".format(
        f" for {duration} seconds" if duration else "", args.interval
    ))
    try:
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                print("Continuous run duration reached; stopping before the next iteration.")
                break
            failed = False
            with run_log("continuous"):
                try:
                    run_definition_iteration()
                except Exception as error:
                    failed = True
                    print(f"Definition iteration failed: {error}")
                    traceback.print_exc()
            if not failed and select_next_opportunity(get_database_path()) is None:
                print("No eligible product definitions remain; stopping continuous run.")
                break
            if deadline is not None and time.monotonic() >= deadline:
                print("Continuous run duration reached; stopping after the completed iteration.")
                break
            wait = args.interval if deadline is None else min(args.interval, max(0, deadline - time.monotonic()))
            print(f"Waiting {wait} seconds before the next iteration...")
            time.sleep(wait)
    except KeyboardInterrupt:
        print("\nContinuous Definition stopped.")


if __name__ == "__main__":
    main()
