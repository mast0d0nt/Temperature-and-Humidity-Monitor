import pathlib
import sqlite3

class DatabaseManager:
    DEFAULT_DB_PATH = pathlib.Path(__file__).resolve().parent.parent / "databases" / "measurements.local.sqlite3"

    def __init__(self, path = DEFAULT_DB_PATH):
        self._path: pathlib.Path = path
        self._connection = sqlite3.connect(self._path)
        self._connection.row_factory = sqlite3.Row

        self.initialize()

    def initialize(self):
        cursor = self._connection.cursor()
        with self._connection:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS measurements (
                    uuid TEXT PRIMARY KEY NOT NULL,
                    timestamp DATETIME NOT NULL,
                    level VARCHAR(16),
                    temperature REAL,
                    humidity REAL,
                    out_of_range_count INTEGER,
                    out_of_range_message VARCHAR(64),
                    error_message VARCHAR(64)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value REAL NOT NULL
                )
            """)
    
    def update_config(self, config: list[tuple]):
        with self._connection:
            self._connection.executemany("""
                INSERT OR REPLACE INTO config (key, value)
                VALUES (?, ?)
            """, config)

    def read(self, limit: int = None):
        cursor = self._connection.cursor()
        if limit is None:
            cursor.execute("""
                SELECT * FROM measurements
                ORDER BY timestamp DESC
            """)
        else:
            cursor.execute("""
                SELECT * FROM measurements
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

        measurements_raw = cursor.fetchall()
        measurements = list(dict(m) for m in measurements_raw)

        return measurements
        

    def write(self, records: list[dict]):
        rows = []

        for record in records:
            uuid = record["uuid"]
            timestamp = record["timestamp"]

            processed = record.get("processed")
            level = processed.get("level")
            temperature = processed.get("temperature")
            humidity = processed.get("humidity")
            out_of_range_count = processed.get("out_of_range_count")
            out_of_range_message = processed.get("out_of_range_message")
            error_message = processed.get("error_message")

            row = (uuid, timestamp, level, temperature, humidity, out_of_range_count, out_of_range_message, error_message)

            rows.append(row)

        cursor = self._connection.cursor()
        with self._connection:
            cursor.executemany("""
                INSERT INTO measurements (uuid, timestamp, level, temperature, humidity, out_of_range_count, out_of_range_message, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)

    def close(self):
        self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()