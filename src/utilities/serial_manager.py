import serial
import time
import uuid
from datetime import datetime, timezone


class SerialManager:
    def __init__(self, port, baudrate=9600, timeout=3):
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._max_number_of_lines = 100
        self._max_empty_lines_in_row = 5

    def process_data(self):
        empty_lines_count = 0
        records = []

        try:
            with serial.Serial(port=self._port, baudrate=self._baudrate, timeout=self._timeout) as board:
                print("Reading data from a board...")
                time.sleep(2)
                board.reset_input_buffer()
                while True:
                    line = board.readline().decode(errors="ignore").strip()

                    if not line:
                        empty_lines_count += 1
                        print(f"Empty lines in a row: {empty_lines_count}")
                        if empty_lines_count >= self._max_empty_lines_in_row:
                            raise TimeoutError("The board is not responding. Stopping reading process...")
                        continue

                    empty_lines_count = 0

                    record = {
                        "id": str(uuid.uuid4()),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "raw": line,
                    }
                    records.append(record)
                    print(line)

                    if len(records) == self._max_number_of_lines:
                        print(
                            f"Number of lines reached the amount restriction ({self._max_number_of_lines}). Stopping reading process..."
                        )
                        break

        except serial.SerialException:
            print(
                f"Port {self._port} is either improperly configured or could not be opened!"
            )
            raise

        except ValueError as exc_value:
            print(
                f"At least one input parameter is out of range! Detailed exception description:\n{exc_value}"
            )
            raise

        except KeyboardInterrupt:
            print(
                "Process execution terminated by a user. Reading process stopped."
            )

        return records
