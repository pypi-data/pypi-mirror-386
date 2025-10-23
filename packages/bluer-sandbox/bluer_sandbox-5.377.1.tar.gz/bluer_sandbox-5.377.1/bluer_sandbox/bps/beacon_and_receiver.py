import asyncio
import socket
import struct
import threading
import time
from bluezero import adapter, advertisement
from bleak import BleakScanner

from bluer_sandbox.logger import logger


# ---------------------------------------------------------------
# Beacon: broadcasts BLE advertisement packets (pure Python)
# ---------------------------------------------------------------
class Beacon:
    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        node_id: str | None = None,
        x: float = 0.0,
        y: float = 0.0,
        sigma: float = 1.0,
        interval_ms: int = 500,
    ):
        """
        node_id: optional short identifier; if None, auto-generate from MAC/hostname.
        x, y: current position estimate (m)
        sigma: position uncertainty (m)
        interval_ms: advertising interval in milliseconds
        """
        ble_adapter = adapter.Adapter()
        if node_id is None:
            # derive unique name from MAC or hostname suffix
            mac_suffix = ble_adapter.address[-5:].replace(":", "")
            node_id = f"UGV-{mac_suffix}"
        self.node_id = node_id

        self.x, self.y, self.sigma = x, y, sigma
        self.interval_ms = interval_ms
        self._adv = None
        self._thread = None
        self._stop = threading.Event()

    def start(self):
        """Start BLE advertising in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"[beacon] {self.node_id} advertising every {self.interval_ms} ms")

    def stop(self):
        """Stop advertising."""
        self._stop.set()
        if self._adv:
            self._adv.stop()
        if self._thread:
            self._thread.join()
        logger.info(f"[beacon] {self.node_id} stopped")

    def _run(self):
        ble_adapter = adapter.Adapter()
        self._adv = advertisement.Advertisement(1, ble_adapter.address)
        self._adv.include_tx_power = True
        self._adv.appearance = 0
        self._adv.local_name = self.node_id

        # Manufacturer payload: 3 floats (x, y, σ)
        payload = struct.pack("<fff", self.x, self.y, self.sigma)
        self._adv.manufacturer_data = {0xFFFF: payload}

        self._adv.start()
        try:
            while not self._stop.is_set():
                time.sleep(self.interval_ms / 1000.0)
        finally:
            self._adv.stop()


# ---------------------------------------------------------------
# Receiver: scans BLE advertisements asynchronously (Bleak)
# ---------------------------------------------------------------
class Receiver:
    def __init__(self, scan_window_s: float = 2.0):
        """
        scan_window_s: duration of each scan iteration
        """
        self.scan_window_s = scan_window_s
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._stop = threading.Event()
        self.latest = {}  # {node_id: (x, y, sigma, rssi, timestamp)}

    def start(self):
        logger.info("[receiver] BLE scanner starting…")
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join()
        logger.info("[receiver] BLE scanner stopped")

    async def _scan_once(self):
        devices = await BleakScanner.discover(
            timeout=self.scan_window_s,
            return_adv=True,
        )
        t = time.time()

        # handle dict / tuple / plain-device variants
        if isinstance(devices, dict):
            iterable = devices.items()
        else:
            first = devices[0] if devices else None
            if isinstance(first, tuple):
                iterable = devices
            else:
                iterable = [
                    (d, getattr(d, "advertisement_data", None)) for d in devices
                ]

        for device, adv_data in iterable:
            name = getattr(adv_data, "local_name", None) or getattr(
                device, "name", None
            )
            if not name:
                continue

            md = getattr(adv_data, "manufacturer_data", None) or {}
            if 0xFFFF in md and len(md[0xFFFF]) >= 12:
                x, y, sigma = struct.unpack("<fff", md[0xFFFF][:12])
                self.latest[name] = (x, y, sigma, getattr(device, "rssi", 0), t)
                logger.info(
                    f"[receiver] {name} → RSSI={device.rssi:>4} dB  "
                    f"pos=({x:.2f},{y:.2f})  σ={sigma:.2f}"
                )

    def _loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while not self._stop.is_set():
            loop.run_until_complete(self._scan_once())


# ---------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------
if __name__ == "__main__":
    # auto-generate unique name per Pi
    beacon = Beacon()
    receiver = Receiver(scan_window_s=3.0)

    try:
        beacon.start()
        receiver.start()
        while True:
            time.sleep(5)
            peers = list(receiver.latest.keys())
            logger.info(f"known peers: {peers if peers else '[]'}")
    except KeyboardInterrupt:
        logger.info("shutting down…")
    finally:
        beacon.stop()
        receiver.stop()
