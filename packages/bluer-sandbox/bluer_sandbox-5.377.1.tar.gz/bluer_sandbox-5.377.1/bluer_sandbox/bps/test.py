#!/usr/bin/env python3

import asyncio
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method
from dbus_next import BusType

from blueness import module

from bluer_sandbox import NAME
from bluer_sandbox.logger import logger

NAME = module.name(__file__, NAME)


class Hello(ServiceInterface):
    def __init__(self):
        super().__init__("org.example.Hello")

    @method()
    def Ping(self) -> "s":
        logger.info(f"{NAME}.ping() called by busctl!")
        return "Pong"


async def main():
    bus = MessageBus(bus_type=BusType.SYSTEM)
    await bus.connect()

    logger.info(f"{NAME}: connected to system bus with unique name: {bus.unique_name}")

    obj_path = "/org/example/Hello"
    bus.export(obj_path, Hello())

    logger.info(f"exported org.example.Hello at {obj_path}")
    logger.info(
        f'run in another terminal: "@bps introspect unique_bus_name={bus.unique_name}"'
    )

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
