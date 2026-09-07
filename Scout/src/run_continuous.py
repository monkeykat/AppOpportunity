"""Continuously run the Scout application one iteration at a time."""

import argparse
import time

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

    app = ScoutApp()
    print(f"Continuous mode enabled; waiting {args.interval} seconds between runs.")

    try:
        while True:
            try:
                app.run()
            except Exception as error:
                print(f"Scout iteration failed: {error}")

            print(f"Waiting {args.interval} seconds before the next iteration...")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nContinuous Scout stopped.")


if __name__ == "__main__":
    main()
