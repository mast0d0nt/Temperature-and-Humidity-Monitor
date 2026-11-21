import logging
import queue
import threading
import time

from serial import Serial, SerialException
from serial.tools import list_ports

logger = logging.getLogger(__name__)


class SerialManager:
    """
    Manages the Arduino Serial connection.

    Responsibilities:
    - Detect the Arduino COM port.
    - Establish and maintain the Serial connection.
    - Read incoming messages in a background thread.
    - Pass raw messages to other components through a queue.
    - Reconnect after connection loss.
    """

    def __init__(
        self,
        port: str | None = None,
        baudrate: int = 9600,
        timeout: float = 1.0,
        reconnect_interval: float = 3.0,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.reconnect_interval = reconnect_interval

        self.messages: queue.Queue[str] = queue.Queue()

        self._serial: Serial | None = None
        self._thread: threading.Thread | None = None

        self._stop_event = threading.Event()
        self._connection_lock = threading.Lock()

        self._connected_port: str | None = None

    @property
    def is_connected(self) -> bool:
        """Return the current connection status."""
        with self._connection_lock:
            return self._serial is not None and self._serial.is_open

    @property
    def connected_port(self) -> str | None:
        """Return the currently connected COM port."""
        with self._connection_lock:
            return self._connected_port

    def start(self) -> None:
        """Start the background Serial reader."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Serial Manager is already running.")
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="SerialReader",
            daemon=True,
        )

        self._thread.start()
        logger.info("Serial Manager started.")

    def stop(self) -> None:
        """Stop the reader and close the Serial connection."""
        self._stop_event.set()

        with self._connection_lock:
            if self._serial is not None:
                try:
                    self._serial.close()
                except SerialException:
                    logger.exception("Error while closing Serial connection.")

                self._serial = None
                self._connected_port = None

        if self._thread is not None:
            self._thread.join(timeout=self.timeout + 2)

        logger.info("Serial Manager stopped.")

    def _run(self) -> None:
        """Main background loop."""
        while not self._stop_event.is_set():
            if not self.is_connected:
                self._connect()

                if not self.is_connected:
                    self._stop_event.wait(self.reconnect_interval)
                    continue

            self._read_messages()

    def _find_port(self) -> str | None:
        """
        Find the Arduino CH340 port.

        If a port is specified manually, use it instead
        of automatic detection.
        """
        if self.port is not None:
            return self.port

        candidates = []

        for port_info in list_ports.comports():
            description = (port_info.description or "").upper()
            manufacturer = (port_info.manufacturer or "").upper()
            hardware_id = (port_info.hwid or "").upper()

            is_ch340 = (
                "CH340" in description
                or "CH340" in manufacturer
                or "1A86:7523" in hardware_id
            )

            if is_ch340:
                candidates.append(port_info.device)

        if len(candidates) == 1:
            return candidates[0]

        if len(candidates) > 1:
            logger.warning(
                "Multiple CH340 devices detected: %s. "
                "Specify the COM port manually.",
                candidates,
            )
            return None

        logger.debug("No CH340 device detected.")
        return None

    def _connect(self) -> None:
        """Establish a Serial connection."""
        port = self._find_port()

        if port is None:
            return

        try:
            connection = Serial(
                port=port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            )

            with self._connection_lock:
                self._serial = connection
                self._connected_port = port

            logger.info("Connected to Arduino on %s.", port)

        except (SerialException, OSError):
            logger.exception("Failed to connect to %s.", port)

    def _read_messages(self) -> None:
        """Read complete newline-terminated Serial messages."""
        buffer = bytearray()

        while not self._stop_event.is_set():
            with self._connection_lock:
                connection = self._serial

            if connection is None or not connection.is_open:
                return

            try:
                chunk = connection.readline()

                if not chunk:
                    continue

                buffer.extend(chunk)


                if not buffer.endswith(b"\n"):
                    continue

                raw_message = buffer.decode(
                    "utf-8",
                    errors="replace",
                ).strip()

                buffer.clear()

                if raw_message:
                    self.messages.put(raw_message)
                    logger.debug("Serial message received: %s", raw_message)

            except (SerialException, OSError):
                logger.exception("Serial connection lost.")
                self._disconnect()
                return

    def _disconnect(self) -> None:
        """Close the current connection."""
        with self._connection_lock:
            if self._serial is not None:
                try:
                    self._serial.close()
                except SerialException:
                    logger.exception("Error during disconnection.")

            self._serial = None
            self._connected_port = None

        logger.warning("Serial connection closed. Reconnection will be attempted.")
