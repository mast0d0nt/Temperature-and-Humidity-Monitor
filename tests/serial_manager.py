import logging

from src.utilities.serial_manager import SerialManager

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def main():
    serial_manager = SerialManager()

    serial_manager.start()

    try:
        print("Waiting for Arduino messages...")

        while True:
            try:
                message = serial_manager.messages.get(timeout=5)
                print(f"Arduino: {message}")

            except Exception as error:
                print(f"Waiting... ({error})")

    except KeyboardInterrupt:
        print("\nStopping Serial Manager...")

    finally:
        serial_manager.stop()


if __name__ == "__main__":
    main()
