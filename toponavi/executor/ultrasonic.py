import time

import wiringpi

class Ultrasonic:
    def __init__(self, pin_config):
        self.trigger_pin = pin_config['trigger']
        self.echo_pin = pin_config['echo']
        wiringpi.pinMode(self.trigger_pin, wiringpi.OUTPUT)
        wiringpi.pinMode(self.echo_pin, wiringpi.INPUT)

    def measure(self):
        """Measure distance in meter
        """
        wiringpi.digitalWrite(self.trigger_pin, 1)
        time.sleep(0.000012)
        wiringpi.digitalWrite(self.trigger_pin, 0)

        count = 0
        while not wiringpi.digitalRead(self.echo_pin):
            count += 1
            if count > 100000:
                break

        t1 = time.time()
        count = 0
        while wiringpi.digitalRead(self.echo_pin):
            count += 1
            if count > 100000:
                break
        t2 = time.time()

        return (t2 - t1) * 340 / 2
