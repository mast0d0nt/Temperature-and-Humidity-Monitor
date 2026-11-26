import pathlib
import sqlite3

from .serial_manager import SerialManager
from .data_parser import DataParser
from .data_collector import DataCollector

class DatabaseManager:
    DEFAULT_DB_PATH = pathlib.Path(__file__).resolve().parent.parent / "databases" / "measurements.sqlite3"

    def __init__(self, serial_manager, data_parser, path = DEFAULT_DB_PATH):
        self._serial_manager: SerialManager = serial_manager
        self._data_parser: DataParser = data_parser
        self._path: pathlib.Path = path
        self._connection = sqlite3.connect(self._path)
        self._connection.row_factory = sqlite3.Row

        self.initialize()

    def initialize(self):
        with self._connection:
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS measurements (
                    uuid UUID PRIMARY KEY,
                    timestamp DATETIME,
                    level VARCHAR(16),
                    temperature REAL,
                    humidity REAL,
                    out_of_range_count INTEGER,
                    out_of_range_message VARCHAR(64),
                    error_message VARCHAR(64)
                )
            """)

    def read(self):
        cursor = self._connection.cursor()
        cursor.execute("""
            SELECT * FROM measurements
        """)

        measurements = cursor.fetchall()

        if measurements:
            for measurement in measurements:
                print(dict(measurement))
        else:
            print("Database is empty")
        

    def write(self, records):
        ...