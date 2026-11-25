import time
from .serial_manager import SerialManager


class DataParser:
    def __init__(self, serial_manager: SerialManager):
        self._serial_manager = serial_manager

    def parse(self):
        records = self._serial_manager.process_data()
        parsed_records = records
        separator = "|"
        thresholds_config = {}

        for record in parsed_records:
            try:
                record_components = record["raw"].split(separator)
                record_level = record_components[0]

                match record_level:
                    case "CONFIG":
                        thresholds_config["MIN_TEMPERATURE_OK"] = float(record_components[1])
                        thresholds_config["MAX_TEMPERATURE_OK"] = float(record_components[2])
                        thresholds_config["MIN_HUMIDITY_OK"] = float(record_components[3])
                        thresholds_config["MAX_HUMIDITY_OK"] = float(record_components[4])
                    case "INFO":
                        record["processed"] = {
                            "level": record_level,
                            "temperature": float(record_components[1]),
                            "humidity": float(record_components[2]),
                        }
                    case "WARNING":
                        if len(record_components[4]) == 0:
                            record["processed"] = {
                                "level": record_level,
                                "temperature": float(record_components[1]),
                                "humidity": float(record_components[2]),
                                "out_of_range_count": int(record_components[3]),
                                "out_of_range_message": "Both parameters are out of range",
                            }
                        else:
                            record["processed"] = {
                                "level": record_level,
                                "temperature": float(record_components[1]),
                                "humidity": float(record_components[2]),
                                "out_of_range_count": int(record_components[3]),
                                "out_of_range_message": record_components[4],
                            }
                    case "ERROR":
                        record["processed"] = {
                            "level": record_level,
                            "error_message": record_components[1],
                        }

                del record["raw"]

            except KeyError:
                print("Records could not be parsed completely (key error)! Try again.")
                time.sleep(2)
                raise

            except IndexError:
                print("Records could not be parsed completely (index error)! Try again.")
                time.sleep(2)
                raise

            except ValueError:
                print("Records could not be parsed completely (value error, values could be converted into another type)! Try again.")
                time.sleep(2)
                raise

            except KeyboardInterrupt:
                print("Process execution terminated by a user. Reading process stopped.")
                time.sleep(1)

        return (thresholds_config, [r for r in parsed_records if "processed" in r])
