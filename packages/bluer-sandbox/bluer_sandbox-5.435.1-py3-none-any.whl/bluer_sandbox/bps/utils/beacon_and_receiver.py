#!/usr/bin/env python3
# beacon_and_receiver.py — alternate BLE advertise/scan cycles using pure BlueZ D-Bus
# Requires: dbus-next, bluetoothd --experimental, adapter powered on.

import asyncio
import struct
import signal
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method, dbus_property
from dbus_next import Variant, BusType, Message, MessageType

from blueness import module
from bluer_options.env import abcli_hostname
from bluer_sandbox import NAME
from bluer_sandbox.logger import logger

NAME = module.name(__file__, NAME)

BUS_NAME = "org.bluez"
ADAPTER_PATH = "/org/bluez/hci0"
ADVERTISING_MGR_IFACE = "org.bluez.LEAdvertisingManager1"
ADAPTER_IFACE = "org.bluez.Adapter1"
AD_OBJECT_PATH = "/org/bluez/example/advertisement0"
AD_IFACE = "org.bluez.LEAdvertisement1"


class Advertisement(ServiceInterface):
    """Minimal LE advertisement implementing org.bluez.LEAdvertisement1"""

    def __init__(self, name: str, x=0.0, y=0.0, sigma=1.0):
        super().__init__(AD_IFACE)
        self._name = name
        self._type = "peripheral"
        self._include_tx_power = True
        self._service_uuids = []
        self._mfg = {0xFFFF: struct.pack("<fff", x, y, sigma)}

    @dbus_property()
    def Type(self) -> "s":
        return self._type

    @Type.setter
    def Type(self, _v):
        pass

    @dbus_property()
    def LocalName(self) -> "s":
        return self._name

    @LocalName.setter
    def LocalName(self, _v):
        pass

    @dbus_property()
    def ServiceUUIDs(self) -> "as":
        return self._service_uuids

    @ServiceUUIDs.setter
    def ServiceUUIDs(self, _v):
        pass

    @dbus_property()
    def IncludeTxPower(self) -> "b":
        return self._include_tx_power

    @IncludeTxPower.setter
    def IncludeTxPower(self, _v):
        pass

    @dbus_property()
    def ManufacturerData(self) -> "a{qv}":
        return {0xFFFF: Variant("ay", self._mfg[0xFFFF])}

    @ManufacturerData.setter
    def ManufacturerData(self, _v):
        pass

    @method()
    def Release(self):
        logger.info(f"{NAME}: BlueZ requested Release()")


async def register_advertisement(bus: MessageBus) -> Advertisement:
    adv = Advertisement(abcli_hostname, x=1.0, y=2.0, sigma=0.5)
    bus.export(AD_OBJECT_PATH, adv)
    await asyncio.sleep(0.5)
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
    try:
        msg = Message(
            destination=BUS_NAME,
            path=ADAPTER_PATH,
            interface=ADVERTISING_MGR_IFACE,
            member="UnregisterAdvertisement",
            signature="o",
            body=[AD_OBJECT_PATH],
        )
        await bus.call(msg)
    except Exception as e:
        logger.warning(f"{NAME}: unregister_advertisement failed: {e}")
    try:
        bus.unexport(AD_OBJECT_PATH, AD_IFACE)
    except Exception:
        pass
    await asyncio.sleep(0.5)


async def advertise_once(bus: MessageBus, duration: float = 2.0):
    """Advertise for a short duration."""
    logger.info(f"{NAME}: starting advertisement...")
    await register_advertisement(bus)
    await asyncio.sleep(duration)
    await unregister_advertisement(bus)
    logger.info(f"{NAME}: stopped advertisement.")


async def start_discovery(bus: MessageBus):
    """Start scanning via org.bluez.Adapter1.StartDiscovery()"""
    msg = Message(
        destination=BUS_NAME,
        path=ADAPTER_PATH,
        interface=ADAPTER_IFACE,
        member="StartDiscovery",
    )
    reply = await bus.call(msg)
    if reply.message_type == MessageType.ERROR:
        logger.warning(f"{NAME}: StartDiscovery failed: {reply.error_name}")


async def stop_discovery(bus: MessageBus):
    """Stop scanning via org.bluez.Adapter1.StopDiscovery()"""
    msg = Message(
        destination=BUS_NAME,
        path=ADAPTER_PATH,
        interface=ADAPTER_IFACE,
        member="StopDiscovery",
    )
    reply = await bus.call(msg)
    if reply.message_type == MessageType.ERROR:
        logger.warning(f"{NAME}: StopDiscovery failed: {reply.error_name}")


async def scan_once(bus: MessageBus, duration: float = 8.0):
    """Scan for nearby BLE devices via D-Bus."""
    logger.info(f"{NAME}: scanning for {duration:.1f}s...")
    devices = {}

    def handle_signal(msg: Message):
        if msg.member != "InterfacesAdded":
            return
        if not msg.body or len(msg.body) < 2:
            return
        _, interfaces = msg.body
        dev_info = interfaces.get("org.bluez.Device1")
        if not dev_info:
            return
        addr = dev_info.get("Address")
        name = dev_info.get("Name") or dev_info.get("Alias")
        if addr and addr not in devices:
            devices[addr] = name or "(unknown)"
            logger.info(f"{NAME}: found {addr} {devices[addr]}")

    bus.add_message_handler(handle_signal)
    await start_discovery(bus)
    await asyncio.sleep(duration)
    await stop_discovery(bus)
    bus.remove_message_handler(handle_signal)
    logger.info(f"{NAME}: found {len(devices)} device(s).")
    await asyncio.sleep(0.5)


async def main():
    bus = MessageBus(bus_type=BusType.SYSTEM)
    await bus.connect()
    logger.info(f"{NAME}: connected to system bus as {bus.unique_name}")

    stop = asyncio.Event()

    def _sigint(*_):
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _sigint)
        except NotImplementedError:
            pass

    try:
        while not stop.is_set():
            await advertise_once(bus, duration=1.0)
            await scan_once(bus, duration=10.0)
    finally:
        await unregister_advertisement(bus)
        logger.info(f"{NAME}: exiting cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
