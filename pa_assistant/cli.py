from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta

from .runner import run_summary, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Personal Activity Tracking Assistant (Phase 1 MVP)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        required=False,
        help="Start date (YYYY-MM-DD, inclusive)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=False,
        help="End date (YYYY-MM-DD, inclusive)",
    )
    parser.add_argument(
        "--period",
        type=str,
        required=False,
        help="Time period: today, yesterday, 7d, this-week, last-week",
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to YAML configuration file (e.g., pa_config.yaml)",
    )
    parser.add_argument(
        "--focus",
        type=str,
        default=None,
        help="Optional focus/topic prompt for the report header.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    args = parse_args()

    if args.period and (args.start_date or args.end_date):
        raise SystemExit("Error: --period and --start-date/--end-date are mutually exclusive.")

    try:
        cfg = load_config(args.config)
        now = datetime.now()
        
        if args.period:
            if args.period == "today":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now
            elif args.period == "yesterday":
                start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
            elif args.period == "7d":
                start_date = now - timedelta(days=7)
                end_date = now
            elif args.period == "this-week":
                days_to_monday = now.weekday()
                start_date = (now - timedelta(days=days_to_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now
            elif args.period == "last-week":
                days_to_monday = now.weekday()
                start_date = (now - timedelta(days=days_to_monday + 7)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = (now - timedelta(days=days_to_monday + 1)).replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                raise SystemExit(f"Error: Unknown period '{args.period}'")

        elif args.start_date and args.end_date:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            # Fallback mapping default_start_offset_days/default_end_offset_days from config
            start_date = (now - timedelta(days=cfg.default_start_offset_days)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = (now - timedelta(days=cfg.default_end_offset_days)).replace(hour=23, minute=59, second=59, microsecond=999999)
    except Exception as exc:
        raise SystemExit(f"Configuration or Date error: {exc}") from exc

    _, _, output_path = run_summary(
        start_date=start_date,
        end_date=end_date,
        config_path=args.config,
        focus_prompt=args.focus,
    )

    # Avoid non-ASCII symbols to prevent encoding issues on some Windows consoles
    print(f"\nSummary generated: {output_path}")


if __name__ == "__main__":
    main()

