import logging
import statistics
from typing import Iterator

import wiringpi

from .motor import Motor

logger = logging.getLogger('controller')

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
