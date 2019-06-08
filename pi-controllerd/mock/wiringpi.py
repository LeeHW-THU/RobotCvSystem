import logging

logger = logging.getLogger('mock-wiringpi')
logger.warning('wiringpi mock in use')

OUTPUT = 'output'

def pinMode(pin, mode):
    logger.debug('pinMode %d %s', pin, mode)

def softPwmCreate(pin, init, max_value):
    logger.debug('softPwmCreate pin: %d, init: %d, max: %d', pin, init, max_value)

def softPwmStop(pin):
    logger.debug('softPwmStop %d', pin)

def softPwmWrite(pin, value):
    logger.debug('softPwmWrite %d %d', pin, value)
