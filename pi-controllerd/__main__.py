import logging
import asyncio
import sys
try:
    import wiringpi
except ImportError:
    from .mock import wiringpi

from .ssdp import SSDPService
from .controller import Controller

logger = logging.getLogger('Main')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    wiringpi.wiringPiSetup()

    loop = asyncio.get_event_loop()

    ssdp = SSDPService()
    async def run_ssdp():
        try:
            await ssdp.start()
        except:
            logger.error('Error in SSDP', exc_info=True)
            sys.exit(1)

    controller = Controller(on_begin=ssdp.stop,
                            on_end=run_ssdp)
    async def run_controller():
        try:
            await controller.start_server()
        except:
            logger.error('Error in Controller', exc_info=True)
            sys.exit(2)

    asyncio.gather(
        run_controller(),
        run_ssdp(),
    )
    loop.run_forever()
