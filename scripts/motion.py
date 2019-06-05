#!/usr/bin/python
import wiringpi
import time

wiringpi.wiringPiSetup()

# init io
# left motor
wiringpi.pinMode(1,1)
wiringpi.softPwmCreate(1,0,100)
wiringpi.softPwmWrite(1,0)

wiringpi.pinMode(4,1)
wiringpi.softPwmCreate(4,0,100)
wiringpi.softPwmWrite(4,0)

# right motor
wiringpi.pinMode(5,1)
wiringpi.softPwmCreate(5,0,100)
wiringpi.softPwmWrite(5,0)

wiringpi.pinMode(6,1)
wiringpi.softPwmCreate(6,0,100)
wiringpi.softPwmWrite(6,0)

print("Motion Demo")

# forward
print("forward")
wiringpi.softPwmWrite(1,0)
wiringpi.softPwmWrite(4,80)

wiringpi.softPwmWrite(5,0)
wiringpi.softPwmWrite(6,80)

time.sleep(0.5)

# backward
print("backward")
wiringpi.softPwmWrite(1,40)
wiringpi.softPwmWrite(4,0)

wiringpi.softPwmWrite(5,40)
wiringpi.softPwmWrite(6,0)

time.sleep(0.5)

# turn left
print("turn left")
wiringpi.softPwmWrite(1,100)
wiringpi.softPwmWrite(4,0)

wiringpi.softPwmWrite(5,0)
wiringpi.softPwmWrite(6,100)

time.sleep(0.4)

print("stop")
wiringpi.softPwmWrite(1,0)
wiringpi.softPwmWrite(4,0)
wiringpi.softPwmWrite(5,0)
wiringpi.softPwmWrite(6,0)

print("End")
