from src.utilities.serial_manager import SerialManager


serial_manager = SerialManager("COM5", 9600, 3)

data = serial_manager.process_data()
print(data)