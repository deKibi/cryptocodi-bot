# crypto_converter/usage_limit_storage.py

# Standard Libraries
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Final


# SQLite storage
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
RATE_LIMIT_DATABASE_PATH: Final[Path] = (
    PROJECT_ROOT / "data" / "rate_limits.sqlite3"
)
SQLITE_TIMEOUT_SECONDS: Final[int] = 10


class UsageLimitStorage:
    """Persist daily usage counters in a local SQLite database."""

    def __init__(self, database_path: Path = RATE_LIMIT_DATABASE_PATH) -> None:
        self._database_path = database_path
        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(
            database=self._database_path,
            timeout=SQLITE_TIMEOUT_SECONDS,
        )

    def _initialize_database(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)

        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rate_limit_usage (
                    usage_date TEXT NOT NULL,
                    counter_type TEXT NOT NULL,
                    subject_id INTEGER NOT NULL,
                    used_units INTEGER NOT NULL CHECK (used_units >= 0),
                    PRIMARY KEY (usage_date, counter_type, subject_id)
                )
                """
            )
            self._migrate_legacy_columns(connection)
            connection.commit()

    @staticmethod
    def _migrate_legacy_columns(connection: sqlite3.Connection) -> None:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(rate_limit_usage)"
            )
        }

        if "scope_type" in columns and "counter_type" not in columns:
            connection.execute(
                "ALTER TABLE rate_limit_usage "
                "RENAME COLUMN scope_type TO counter_type"
            )

        if "scope_id" in columns and "subject_id" not in columns:
            connection.execute(
                "ALTER TABLE rate_limit_usage "
                "RENAME COLUMN scope_id TO subject_id"
            )

    def try_acquire(
        self,
        usage_date: date,
        counter_type: str,
        subject_id: int,
        units: int,
        limit: int,
    ) -> bool:
        """Atomically add usage units when the daily limit allows it."""
        if units <= 0:
            raise ValueError("units must be greater than zero")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        if not counter_type:
            raise ValueError("counter_type must not be empty")

        if units > limit:
            return False

        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO rate_limit_usage (
                    usage_date,
                    counter_type,
                    subject_id,
                    used_units
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT (usage_date, counter_type, subject_id)
                DO UPDATE SET used_units = used_units + excluded.used_units
                WHERE used_units + excluded.used_units <= ?
                """,
                (
                    usage_date.isoformat(),
                    counter_type,
                    subject_id,
                    units,
                    limit,
                ),
            )
            connection.commit()

            return cursor.rowcount == 1

    def release(
        self,
        usage_date: date,
        counter_type: str,
        subject_id: int,
        units: int,
    ) -> None:
        """Atomically release usage units without going below zero."""
        if units <= 0:
            raise ValueError("units must be greater than zero")

        if not counter_type:
            raise ValueError("counter_type must not be empty")

        with closing(self._connect()) as connection:
            connection.execute(
                """
                UPDATE rate_limit_usage
                SET used_units = MAX(used_units - ?, 0)
                WHERE usage_date = ?
                    AND counter_type = ?
                    AND subject_id = ?
                """,
                (
                    units,
                    usage_date.isoformat(),
                    counter_type,
                    subject_id,
                ),
            )
            connection.commit()
