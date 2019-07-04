import time
import logging
import pathlib

import yaml
import wiringpi

from .ultrasonic import Ultrasonic
from .state import StateController

logger = logging.getLogger('main')

def main():
    wiringpi.wiringPiSetup()

    with (pathlib.Path(__file__).parent/'config.yml').open('r', newline='') as ymlfile:
        config = yaml.safe_load(ymlfile)

    CONTROL_INTERVAL = config['control_interval']

    controller = StateController(config)
    ultrasonic = Ultrasonic(config['pins']['ultrasonic'])

    controller.start()

    start_time = time.time()
    try:
        while True:
            distance = ultrasonic.measure()
            controller.ultrasonic(distance)

            now = time.time()
            time_remains = start_time + CONTROL_INTERVAL - now
            if time_remains > 0:
                time.sleep(time_remains)
                start_time += CONTROL_INTERVAL
            else:
                start_time = now
                logger.warning('Overrun control interval by %f seconds', -time_remains)
    except:
        controller.stop()
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
