import logging
import asyncio
try:
    import wiringpi
except ImportError:
    from .mock import wiringpi

from .ssdp import SSDPService
from .controller import Controller

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    wiringpi.wiringPiSetup()

    loop = asyncio.get_event_loop()

    ssdp = SSDPService()
    asyncio.ensure_future(ssdp.start())

    controller = Controller(on_begin=ssdp.stop,
                            on_end=ssdp.start)
    asyncio.ensure_future(controller.start_server())

    loop.run_forever()
