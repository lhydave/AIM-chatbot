#!/usr/bin/env python3
"""
Command-line application for running the automated marking workflow.
"""

import sys
import argparse
import asyncio
from pathlib import Path
from auto_marker.marker import Marker


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the automated marking workflow for student submissions.")

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="./auto_marker/my_marker_config.toml",
        help="Path to the marker configuration file (default: ./auto_marker/my_marker_config.toml)",
    )

    # Step selection arguments
    step_group = parser.add_argument_group("workflow steps")
    step_group.add_argument(
        "--download",
        action="store_true",
        help="Download submissions from OpenReview",
    )
    step_group.add_argument(
        "--reference",
        action="store_true",
        help="Load reference materials",
    )
    step_group.add_argument(
        "--process",
        action="store_true",
        help="Process submissions",
    )
    step_group.add_argument(
        "--mark",
        action="store_true",
        help="Mark submissions",
    )
    step_group.add_argument(
        "--post",
        action="store_true",
        help="Post marks to OpenReview",
    )

    parser.add_argument(
        "-l",
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    return parser.parse_args()


async def main() -> None:
    """Main entry point for the command-line application."""
    args = parse_arguments()

    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)

    # Build the steps string based on selected flags
    selected_steps = []
    if args.download:
        selected_steps.append("download")
    if args.reference:
        selected_steps.append("reference")
    if args.process:
        selected_steps.append("process")
    if args.mark:
        selected_steps.append("mark")
    if args.post:
        selected_steps.append("post")

    # Require at least one step to be specified
    if not selected_steps:
        print("Error: You must specify at least one step to run.")
        print("Use one or more of: --download, --reference, --process, --mark, --post")
        sys.exit(1)

    steps = "+".join(selected_steps)

    print(f"Using configuration file: {config_path}")
    print(f"Running steps: {steps}")
    print(f"Log level: {args.log_level}")

    try:
        # Initialize and run the marker
        marker = Marker(str(config_path))
        await marker.run(steps=steps, log_level=args.log_level)
        print("Marking workflow completed successfully.")
    except Exception as e:
        print(f"Error during marking workflow: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
