import wiringpi

class Motor:
    MAX_PWM = 100

    def __init__(self, pin_config):
        self.forward_pin = pin_config['forward']
        self.backward_pin = pin_config['backward']
        self.started = False

    def _pins(self):
        yield self.forward_pin
        yield self.backward_pin

    def start(self):
        if self.started:
            return
        for pin in self._pins():
            wiringpi.pinMode(pin, wiringpi.OUTPUT)
            wiringpi.softPwmCreate(pin, 0, self.MAX_PWM)
        self.started = True

    def stop(self):
        for pin in self._pins():
            wiringpi.softPwmStop(pin)
        self.started = False

    @classmethod
    def _write_pwm(cls, pin, value):
        if value == 0:
            wiringpi.softPwmWrite(pin, 0)
        else:
            wiringpi.softPwmWrite(pin, int(round(value * cls.MAX_PWM)))

    def input(self, power: float):
        """Set motor output power

        power: [-1.0, 1.0], positive value means forward, negative neams backward.
        """
        if not self.started:
            raise RuntimeError('Call start frist')
        if power > 1. or power < -1.:
            raise ValueError('power {} should between -1 and 1'.format(power))
        if power > 0:
            self._write_pwm(self.forward_pin, power)
            self._write_pwm(self.backward_pin, 0)
        else:
            self._write_pwm(self.forward_pin, 0)
            self._write_pwm(self.backward_pin, -power)
