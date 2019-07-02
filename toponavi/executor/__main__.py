import time
import statistics
import logging
import csv
import pathlib
from typing import Iterator

import yaml
import wiringpi

from .ultrasonic import Ultrasonic
from .motor import Motor

logger = logging.getLogger('executor')

class DifferentialController:
    def __init__(self, pin_config: dict):
        self.left_motor = Motor(pin_config['left'])
        self.right_motor = Motor(pin_config['right'])

    def _motors(self) -> Iterator[Motor]:
        yield self.left_motor
        yield self.right_motor

    def start(self):
        for m in self._motors():
            m.start()

    def stop(self):
        for m in self._motors():
            m.stop()

    def command(self, speed: float, turn: float):
        turn = min(max(-1.0, turn), 1.0)

        left = speed - turn
        right = speed + turn

        if turn > 0:
            small = left
            large = right
        else:
            small = right
            large = left

        offset = 0
        if small < -1:
            offset = -1 - small
        elif large > 1:
            offset = 1 - large

        self.left_motor.input(left + offset)
        self.right_motor.input(right + offset)

class MedianFilter:
    def __init__(self, config):
        self.window_size = config['window_size']
        self.window = []

    def next(self, new_data: float):
        self.window.append(new_data)
        if len(self.window) > self.window_size:
            self.window.pop(0)
        return statistics.median(self.window)

class PID:
    def __init__(self, config, sample_interval=0.1):
        self.kp = config['kp']
        self.ti = config['ti'] / sample_interval
        self.td = config['td'] / sample_interval

        self.i = 0
        self.last_error = None

    def error_sample(self, error: float):
        self.i += error
        d = error - self.last_error if self.last_error is not None else 0
        self.last_error = error

        return self.kp * (error + self.i / self.ti + d * self.td)

def main():
    wiringpi.wiringPiSetup()

    with (pathlib.Path(__file__).parent/'config.yml').open('r', newline='') as ymlfile:
        config = yaml.load(ymlfile)

    CONTROL_INTERVAL = config['control_interval']
    DISTANCE_SETPOINT = config['distance_setpoint']
    SPEED_SETPOINT = config['speed']

    ultrasonic = Ultrasonic(config['pins']['ultrasonic'])
    distance_filter = MedianFilter(config['normal_mode']['median_filter'])
    controller = DifferentialController(config['pins']['motor'])
    pid = PID(config['normal_mode']['pid'])

    controller.start()

    start_time = time.time()
    log_file = open('executor_log_{}.csv'.format(round(time.time())), 'w', newline='')
    log_writer = csv.DictWriter(log_file, ['time', 'distance', 'distance_filtered', 'turn_command', 'pid.i'])
    log_writer.writeheader()
    try:
        while True:
            distance = ultrasonic.measure()
            distance_filtered = distance_filter.next(distance)
            turn = pid.error_sample(distance_filtered - DISTANCE_SETPOINT)
            controller.command(SPEED_SETPOINT, turn)

            state = {
                'time': start_time,
                'distance': distance,
                'distance_filtered': distance_filtered,
                'turn_command': turn,
                'pid.i': pid.i,
            }

            logger.debug("distance: %.4f (filtered: %.4f); turn: %.4f; pid.i: %.4f",
                         distance, distance_filtered, turn, pid.i)
            log_writer.writerow(state)

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
