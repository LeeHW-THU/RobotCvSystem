import math
import time
import logging

from .controller import DifferentialController, MedianFilter, PID
from .distancestatistics import DistanceStatisics

logger = logging.getLogger('state')

class SimpleStateFactory:
    def __init__(self, state_class, config):
        self._state_class = state_class
        self._state_config = config

    def __call__(self):
        return self._state_class(self._state_config)

class StateRunContext:
    def __init__(self, state_factories: dict, distance_statistics: DistanceStatisics):
        self._state_factories = state_factories
        self.distance_statistics = distance_statistics
        self.last_ultrasonic_reading = None # filtered
        self.state = None
        self.turn_command = None

    def to_state(self, state_class):
        logger.info("Transfering from %s to %s", type(self.state).__name__, state_class.__name__)
        self.state = self._state_factories[state_class]()

    def ultrasonic_reading(self, reading):
        self.last_ultrasonic_reading = reading
        self.distance_statistics.data(reading)

    def tick(self):
        self.state.tick(self)
        logger.debug('tick. dist: k %.3f c %.3f e %.3e. turn: %.3f',
                     self.distance_statistics.aproching_rate,
                     self.distance_statistics.latest,
                     self.distance_statistics.squared_error,
                     self.turn_command)

class State:
    def __init__(self, config):
        pass

    def tick(self, context: StateRunContext):
        raise NotImplementedError()

class NormalState(State):
    def __init__(self, config):
        super().__init__(config)
        self.disturb_squared_error_thre = config['disturb_squared_error_thre']
        self._distance_setpoint_config = config['distance_setpoint']
        self._bias_timeout_config = config['bias_timeout']
        self.distance_setpoint_bias(0)
        self.pid = PID(config['pid'], config['control_interval'])

    def distance_setpoint_bias(self, bias):
        self.distance_setpoint = self._distance_setpoint_config + bias
        if bias != 0:
            self.bias_timeout = time.time() + self._bias_timeout_config
        else:
            self.bias_timeout = float('inf')
        logger.debug('distance_setpoint: %.3f', self.distance_setpoint)

    def tick(self, context: StateRunContext):
        if context.distance_statistics.squared_error > self.disturb_squared_error_thre:
            context.to_state(DisturbedState)
            context.turn_command = 0
            return

        context.turn_command = self.pid.error_sample(context.last_ultrasonic_reading - self.distance_setpoint)
        if time.time() > self.bias_timeout:
            context.to_state(StabilizedState)
            context.state.no_bias()
            context.tick()

class StabilizedState(State):
    """
    Transit state, always transfer to next state on next tick
    """
    def __init__(self, config):
        super().__init__(config)
        self.max_bias = config['max_bias']
        self.min_bias = config['min_bias']
        self.max_no_bias = config['max_no_bias']
        self.min_no_bias = config['min_no_bias']
        self._distance_setpoint = config['distance_setpoint']
        self.speed = config['speed']
        self.aproching_angle = config['aproching_angle']
    def no_bias(self):
        self.max_bias = self.max_no_bias
        self.min_bias = self.min_no_bias
    def tick(self, context: StateRunContext):
        bias = context.distance_statistics.latest - self._distance_setpoint
        if bias < self.min_bias:
            bias = self.min_bias
        if bias < self.max_bias:
            context.to_state(NormalState)
            if bias > self.max_no_bias or bias < self.min_no_bias:
                context.state.distance_setpoint_bias(bias)
        else:
            context.to_state(TurnState)
            current_angle = math.atan2(context.distance_statistics.aproching_rate, self.speed)
            context.state.angle(-current_angle - self.aproching_angle)

class DisturbedState(State):
    def __init__(self, config):
        super().__init__(config)
        self.disturb_squared_error_thre = config['disturb_squared_error_thre']
        self.silent_end = time.time() + config['initial_silent']
        self.to_normal_time = time.time() + config['to_normal_time']
        self.blind_thre = config['blind_thre']
        self._initial = False

    def initial(self):
        self._initial = True

    def tick(self, context: StateRunContext):
        context.turn_command = 0.0
        now = time.time()
        if now < self.silent_end:
            return
        if context.last_ultrasonic_reading > self.blind_thre:
            context.to_state(BlindState)
            return
        if context.distance_statistics.squared_error > self.disturb_squared_error_thre:
            context.to_state(ChaosState)
            return
        if self._initial or now >= self.to_normal_time:
            context.to_state(StabilizedState)
            if self._initial:
                context.state.no_bias()
            context.tick()
            return

class ChaosState(State):
    def __init__(self, config):
        super().__init__(config)
        self.disturb_squared_error_thre = config['disturb_squared_error_thre']
        self.distance_setpoint = config['distance_setpoint']
        self.pid = PID(config['pid'], config['control_interval'])
        self._to_normal_time_config = config['to_normal_time']
        self._reset_to_normal_time()

    def _reset_to_normal_time(self):
        self.to_normal_time = time.time() + self._to_normal_time_config

    def tick(self, context: StateRunContext):
        context.turn_command = self.pid.error_sample(context.last_ultrasonic_reading - self.distance_setpoint)
        if context.distance_statistics.squared_error > self.disturb_squared_error_thre:
            self._reset_to_normal_time()
        now = time.time()
        if now >= self.to_normal_time:
            context.to_state(StabilizedState)
            context.tick()
            return

class TurnState(State):
    def __init__(self, config):
        super().__init__(config)
        self.omega = config['omega']
        self.alpha = config['alpha']
        self.turn_command_abs = config['turn_command']
        self._turn_command = None
        self._end_time = None
        self._angle = None

    def angle(self, angle):
        logger.debug('Turning angle %.4f', angle)
        self._turn_command = self.turn_command_abs if angle > 0 else - self.turn_command_abs
        self._angle = angle

    def tick(self, context: StateRunContext):
        if self._angle is None:
            raise RuntimeError('call angle first')
        now = time.time()
        if self._end_time is None:
            context.turn_command = self._turn_command
            # 假设匀加速，匀速，匀减速运动，由运动学公式：
            # time = angle/ω + ω/α (angle >= ω^2/α)
            #        2*sqrt(angle/α) otherwise
            angle_abs = abs(self._angle)
            if angle_abs > self.omega ** 2 / self.alpha:
                time_needed = angle_abs / self.omega + self.omega / self.alpha
            else:
                time_needed = 2 * math.sqrt(angle_abs / self.alpha)
            logger.debug('turn time needed: %.2f', time_needed)
            self._end_time = now + time_needed
        if now >= self._end_time:
            context.turn_command = 0.0
            context.to_state(DisturbedState)
            context.state.initial()

class BlindState(State):
    def __init__(self, config):
        super().__init__(config)
        self.restore_thre = config['restore_thre']

    def tick(self, context: StateRunContext):
        context.turn_command = 0
        if context.last_ultrasonic_reading < self.restore_thre:
            context.to_state(DisturbedState)

class StateController:
    def __init__(self, config):
        self.speed_command = config['speed_command']

        states = [
            (NormalState, 'normal_state'),
            (DisturbedState, 'disturbed_state'),
            (StabilizedState, 'stablized_state'),
            (ChaosState, 'chaos_state'),
            (TurnState, 'turn_state'),
            (BlindState, 'blind_state'),
        ]
        for s in states:
            for c in ['control_interval', 'distance_setpoint']:
                config[s[1]][c] = config[c]

        self._diff_controller = DifferentialController(config['pins']['motor'])
        self._filter = MedianFilter(config['median_filter'])

        state_factories = {c: SimpleStateFactory(c, config[k]) for (c, k) in states}
        ds = DistanceStatisics(config['distance_statisics'], config['control_interval'])
        self._context = StateRunContext(state_factories, ds)

    def ultrasonic(self, reading):
        filtered = self._filter.next(reading)
        logger.debug('ultrasonic reading %.4f (filtered: %.4f)', reading, filtered)
        self._context.ultrasonic_reading(filtered)
        self.tick()

    def turn(self, angle):
        self._context.to_state(TurnState)
        self._context.state.angle(angle)
        self.tick()

    def start(self):
        self._diff_controller.start()
        self._context.to_state(DisturbedState)
        self._context.state.initial()

    def stop(self):
        self._diff_controller.stop()

    def tick(self):
        self._context.tick()
        self._diff_controller.command(self.speed_command, self._context.turn_command)
