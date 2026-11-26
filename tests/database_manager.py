from src.utilities.serial_manager import SerialManager
from src.utilities.data_parser import DataParser
from src.utilities.database_manager import DatabaseManager

serial_manager = SerialManager("COM5")
data_parser = DataParser(serial_manager=serial_manager)
database_manager = DatabaseManager(serial_manager=serial_manager, data_parser=data_parser)

database_manager.read()