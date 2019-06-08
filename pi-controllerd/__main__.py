import logging
import asyncio
try:
    import wiringpi
except ImportError:
    from .mock import wiringpi

from .ssdp import SSDPService
from .controller import Controller

logger = logging.getLogger('Main')

async def main():
    logging.basicConfig(level=logging.INFO)
    wiringpi.wiringPiSetup()

    ssdp = SSDPService()

    controller = Controller(on_begin=ssdp.stop)

    await controller.start_server()
    while True:
        await ssdp.run() # SSDP should only stop when controller is connected
        if controller.connection_task: # In case of connection is very short living
            await controller.connection_task

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
