import asyncio
from bleak import BleakScanner


async def main():
    print("LE Scan ...")

    def cb(d, ad):
        name = d.name or ""
        print(f"{d.address} {name}".strip())

    await BleakScanner.discover(timeout=10.0, detection_callback=cb)


if __name__ == "__main__":
    asyncio.run(main())
