from .serial_manager import SerialManager
from .data_parser import DataParser
from .database_manager import DatabaseManager

import argparse
import pathlib


class DataCollector:
    def __init__(self):
        pass

    @staticmethod
    def collect():
        parser = argparse.ArgumentParser("MonitorParser", description="Parses arguments to communicate with SerialManager/DatabaseManager")
        parser.add_argument("-p", "--port", help="set port for board", type=str, required=True)
        parser.add_argument("-b", "--baudrate", default=9600, help="set baudrate for board", type=int)
        parser.add_argument("-t", "--timeout", default=3, help="set timeout for board", type=float)
        parser.add_argument("-d", "--db-path", help="set database path for writing records", default=DatabaseManager.DEFAULT_DB_PATH, type=pathlib.Path)

        args = parser.parse_args()

        serial_manager = SerialManager(args.port, args.baudrate, args.timeout)
        raw_records = serial_manager.read()

        data_parser = DataParser()
        parsed_records = data_parser.parse(raw_records)

        parsed_records_config = list(parsed_records[0].items())
        parsed_records_list = parsed_records[1]

        with DatabaseManager(args.db_path) as database_manager:
            database_manager.update_config(parsed_records_config)
            database_manager.write(parsed_records_list)

            print(database_manager.read(5))


if __name__ == "__main__":
    DataCollector.collect()