import time
import asyncio
import logging

from .state import StateController
from .ultrasonic import Ultrasonic

logger = logging.getLogger('executor')

class Executor:
    def __init__(self, config):
        self._control_interval = config['control_interval']
        self.controller = StateController(config)
        self.ultrasonic = Ultrasonic(config['pins']['ultrasonic'])

    async def run(self):
        self.controller.start()
        start_time = time.time()
        try:
            while True:
                distance = self.ultrasonic.measure()
                self.controller.ultrasonic(distance)

                now = time.time()
                time_remains = start_time + self._control_interval - now
                if time_remains > 0:
                    await asyncio.sleep(time_remains)
                    start_time += self._control_interval
                else:
                    start_time = now
                    logger.warning('Overrun control interval by %f seconds', -time_remains)
        except:
            self.controller.stop()
            raise
