#!/usr/bin/env python3
# beacon.py — BLE advertiser via BlueZ D-Bus (no Bluezero/Bleak)
# Requires: dbus-next 0.2.x, bluetoothd --experimental, adapter powered on.

import asyncio
import argparse
import struct
import signal
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method, dbus_property
from dbus_next import Variant, BusType, Message, MessageType

from blueness import module
from bluer_options import string
from bluer_options.env import abcli_hostname

from bluer_sandbox import NAME
from bluer_sandbox.logger import logger

NAME = module.name(__file__, NAME)

# ---- BlueZ constants
BUS_NAME = "org.bluez"
ADAPTER_PATH = "/org/bluez/hci0"
ADVERTISING_MGR_IFACE = "org.bluez.LEAdvertisingManager1"
AD_OBJECT_PATH = "/org/bluez/example/advertisement0"  # any unique path is fine
AD_IFACE = "org.bluez.LEAdvertisement1"


class Advertisement(ServiceInterface):
    """
    Minimal LE advertisement implementing org.bluez.LEAdvertisement1
    with:
      - Type           : "peripheral"
      - LocalName      : e.g., "TEST-PI"
      - IncludeTxPower : True
      - ManufacturerData (0xFFFF): 3 floats (x,y,sigma) as little-endian
    """

    def __init__(self, name: str, x=0.0, y=0.0, sigma=1.0):
        super().__init__(AD_IFACE)
        self._name = name
        self._type = "peripheral"
        self._include_tx_power = True
        self._service_uuids = []  # keep empty for raw ADV + manufacturer payload
        self._mfg = {0xFFFF: struct.pack("<fff", x, y, sigma)}

    # ---- Required properties (older dbus-next may treat them as writable; add no-op setters)

    @dbus_property()
    def Type(self) -> "s":
        return self._type

    @Type.setter
    def Type(self, _value: "s"):
        pass  # BlueZ never writes this; satisfy older dbus-next

    @dbus_property()
    def LocalName(self) -> "s":
        return self._name

    @LocalName.setter
    def LocalName(self, _value: "s"):
        pass

    @dbus_property()
    def ServiceUUIDs(self) -> "as":
        return self._service_uuids

    @ServiceUUIDs.setter
    def ServiceUUIDs(self, _value: "as"):
        pass

    @dbus_property()
    def IncludeTxPower(self) -> "b":
        return self._include_tx_power

    @IncludeTxPower.setter
    def IncludeTxPower(self, _value: "b"):
        pass

    @dbus_property()
    def ManufacturerData(self) -> "a{qv}":
        # value must be Variant("ay", <bytes>)
        return {0xFFFF: Variant("ay", self._mfg[0xFFFF])}

    @ManufacturerData.setter
    def ManufacturerData(self, _value: "a{qv}"):
        pass

    # ---- Optional method BlueZ may call when it drops the ad
    @method()
    def Release(self):
        logger.info("blueZ requested Release() — advertisement unregistered.")


async def register_advertisement(
    bus: MessageBus,
    x: float,
    y: float,
    sigma: float,
):
    logger.info(
        "registering advertisement: {}".format(
            ", ".join(
                [
                    f"x: {x:.2f}",
                    f"y: {y:.2f}",
                    f"sigma: {sigma:.2f}",
                ]
            )
        )
    )

    # Export our advertisement object on the system bus
    adv = Advertisement(
        name=abcli_hostname,
        x=x,
        y=y,
        sigma=sigma,
    )
    bus.export(AD_OBJECT_PATH, adv)

    # Give dbus-next a moment to publish before BlueZ introspects it
    await asyncio.sleep(1.0)

    # Call BlueZ: RegisterAdvertisement(object_path, dict)
    msg = Message(
        destination=BUS_NAME,
        path=ADAPTER_PATH,
        interface=ADVERTISING_MGR_IFACE,
        member="RegisterAdvertisement",
        signature="oa{sv}",
        body=[AD_OBJECT_PATH, {}],
    )
    reply = await bus.call(msg)
    if reply.message_type == MessageType.ERROR:
        raise RuntimeError(f"RegisterAdvertisement failed: {reply.error_name}")

    return adv


async def unregister_advertisement(bus: MessageBus):
    msg = Message(
        destination=BUS_NAME,
        path=ADAPTER_PATH,
        interface=ADVERTISING_MGR_IFACE,
        member="UnregisterAdvertisement",
        signature="o",
        body=[AD_OBJECT_PATH],
    )
    await bus.call(msg)


async def main(
    x: float,
    y: float,
    sigma: float,
    spacing: float = 2.0,
):
    # Connect to the SYSTEM bus (the one BlueZ uses)
    bus = MessageBus(bus_type=BusType.SYSTEM)
    await bus.connect()
    logger.info(f"connected to system bus as {bus.unique_name}")

    # Register with BlueZ
    try:
        await register_advertisement(
            bus=bus,
            x=x,
            y=y,
            sigma=sigma,
        )
    except Exception as e:
        logger.error(f"failed to start advertising: {e}")
        return

    logger.info(
        f"advertising as '{abcli_hostname}'"
        " (manuf 0xFFFF: <x,y,sigma>) - ^C to stop."
    )

    # Handle Ctrl+C to cleanly unregister
    stop = asyncio.Event()

    def _sigint(*_):
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _sigint)
        except NotImplementedError:
            pass  # Windows, or limited envs

    # Heartbeat
    try:
        while not stop.is_set():
            logger.info(f"advertising {abcli_hostname} ...")
            await asyncio.sleep(spacing)
    finally:
        try:
            await unregister_advertisement(bus)
            logger.info("unregistered advertisement.")
        except Exception as e:
            logger.error(f"cannot unregister: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(NAME)
    parser.add_argument(
        "--x",
        type=float,
        default=1.0,
    )
    parser.add_argument(
        "--y",
        type=float,
        default=2.0,
    )
    parser.add_argument(
        "--sigma",
        type=float,
        default=3.0,
    )
    parser.add_argument(
        "--spacing",
        type=float,
        default=2.0,
        help="in seconds.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10,
        help="in seconds, -1: infinite.",
    )
    args = parser.parse_args()

    logger.info(
        "{}: every {}{}.".format(
            NAME,
            string.pretty_duration(
                args.spacing,
                short=True,
            ),
            (
                ""
                if args.timeout == -1
                else " for {}".format(
                    string.pretty_duration(
                        args.timeout,
                        short=True,
                    )
                )
            ),
        )
    )

    async def runner():
        task = asyncio.create_task(
            main(
                x=args.x,
                y=args.y,
                sigma=args.sigma,
                spacing=args.spacing,
            )
        )
        try:
            if args.timeout > 0:
                await asyncio.wait_for(task, timeout=args.timeout)
            else:
                await task
        except asyncio.TimeoutError:
            logger.info(
                "timeout ({}) reached, stopping advertisement.".format(
                    string.pretty_duration(
                        args.timeout,
                        short=True,
                    )
                )
            )
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    asyncio.run(runner())
