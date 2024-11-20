from __future__ import annotations

import argparse

from app.data_store import DEFAULT_DB_PATH, EmployeeAnalyticsStore
from app.settings import load_settings
from app.ui import EmployeeAnalyticsApp
from app.web import run_web_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Employee Data Analytics demo app")
    parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Seed sample data if the local database is empty.",
    )
    parser.add_argument(
        "--reset-sample",
        action="store_true",
        help="Replace local data with a fresh sample dataset before launching.",
    )
    parser.add_argument(
        "--empty",
        action="store_true",
        help="Start with an empty local database if no data exists.",
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help=f"SQLite database path. Default: {DEFAULT_DB_PATH}",
    )
    parser.add_argument(
        "--desktop",
        action="store_true",
        help="Launch the Tkinter desktop UI instead of the web UI.",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Host for web UI. Default comes from data/app_config.json.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port for web UI. Default comes from data/app_config.json.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Start the web server without opening a browser.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    store = EmployeeAnalyticsStore(args.db)
    seed_sample = args.sample_data or (settings.default_sample_data and not args.empty)
    store.initialize(seed_sample=seed_sample, reset_sample=args.reset_sample)
    if args.desktop:
        app = EmployeeAnalyticsApp(store, sample_mode=seed_sample or args.reset_sample)
        app.mainloop()
        return

    run_web_app(
        store,
        host=args.host or settings.host,
        port=args.port or settings.port,
        open_browser=not args.no_browser,
    )


if __name__ == "__main__":
    main()
