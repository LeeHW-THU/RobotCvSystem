import asyncio
import logging
import pathlib

import yaml
import wiringpi

from ..executor import Executor

logger = logging.getLogger('main')

class MockUltrasonic:
    def __init__(self, reading):
        self._reading = reading

    def measure(self):
        return self._reading

async def main():
    wiringpi.wiringPiSetup()

    with (pathlib.Path(__file__).parent.parent/'config.yml').open('r', newline='') as ymlfile:
        config = yaml.safe_load(ymlfile)
    executor = Executor(config)
    executor.ultrasonic = MockUltrasonic(30.0)
    run_task = asyncio.ensure_future(executor.run())
    await asyncio.sleep(0.5)
    executor.controller.turn(1.57)
    await run_task

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
