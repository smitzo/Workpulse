"""Compatibility launcher for the Employee Data Analytics app.

The project used to launch an activity-log/MySQL screen from this file. The
current app is modular and SQLite-backed, so running this file
now starts the same application as main.py.
"""

from main import main


if __name__ == "__main__":
    main()
