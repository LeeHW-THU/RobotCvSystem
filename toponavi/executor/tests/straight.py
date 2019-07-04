import asyncio
import logging
import pathlib

import yaml
import wiringpi

from ..executor import Executor

logger = logging.getLogger('main')

async def main():
    wiringpi.wiringPiSetup()

    with (pathlib.Path(__file__).parent.parent/'config.yml').open('r', newline='') as ymlfile:
        config = yaml.safe_load(ymlfile)
    executor = Executor(config)
    await executor.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
