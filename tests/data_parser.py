from src.utilities.serial_manager import SerialManager
from src.utilities.data_parser import DataParser


serial_manager = SerialManager("COM5", 9600, 3)
data_parser = DataParser(serial_manager)

print(data_parser.parse())