#!/usr/bin/python
import wiringpi
import time

wiringpi.wiringPiSetup()
TOP_SPEED = 100
SENSITIVITY = 0.2
def init_motor():
    # init io
    # left motor
    wiringpi.pinMode(1,1)
    wiringpi.softPwmCreate(1,0,TOP_SPEED)
    wiringpi.softPwmWrite(1,0)

    wiringpi.pinMode(4,1)
    wiringpi.softPwmCreate(4,0,TOP_SPEED)
    wiringpi.softPwmWrite(4,0)

    # right motor
    wiringpi.pinMode(5,1)
    wiringpi.softPwmCreate(5,0,TOP_SPEED)
    wiringpi.softPwmWrite(5,0)

    wiringpi.pinMode(6,1)
    wiringpi.softPwmCreate(6,0,TOP_SPEED)
    wiringpi.softPwmWrite(6,0)

# motor id and direction:
#   1: left go forward
#   4: left go backward
#   5: right go forwad 
#   6: right go backward
def stop():
    wiringpi.softPwmWrite(1,0)
    wiringpi.softPwmWrite(4,0)
    wiringpi.softPwmWrite(5,0)
    wiringpi.softPwmWrite(6,0)

def turn_left(turn_speed):
    # print("Turn Speed: ",int(turn_speed*TOP_SPEED))
    wiringpi.softPwmWrite(4,0)
    wiringpi.softPwmWrite(5,int(turn_speed*TOP_SPEED))
    wiringpi.softPwmWrite(1,0)
    wiringpi.softPwmWrite(6,0)
    time.sleep(SENSITIVITY)
    stop()

def turn_right(turn_speed):
    wiringpi.softPwmWrite(4,0)
    wiringpi.softPwmWrite(5,0)
    wiringpi.softPwmWrite(1,int(turn_speed*TOP_SPEED))
    wiringpi.softPwmWrite(6,0)
    time.sleep(SENSITIVITY)
    stop()

def go_forward(speed):
    wiringpi.softPwmWrite(4,0)
    wiringpi.softPwmWrite(5,int(speed*TOP_SPEED))
    wiringpi.softPwmWrite(1,int(speed*TOP_SPEED))
    wiringpi.softPwmWrite(6,0)
    time.sleep(SENSITIVITY)
    stop()

def go_backward(speed):
    wiringpi.softPwmWrite(4,int(speed*TOP_SPEED))
    wiringpi.softPwmWrite(5,0)
    wiringpi.softPwmWrite(1,0)
    wiringpi.softPwmWrite(6,int(speed*TOP_SPEED))
    time.sleep(SENSITIVITY)
    stop()

# read key
import sys
import tty
import termios

def readchar():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def readkey(getchar_fn=None):
    getchar = getchar_fn or readchar
    c1 = getchar()
    if ord(c1) != 0x1b:
        return c1
    c2 = getchar()
    if ord(c2) != 0x5b:
        return c1
    c3 = getchar()
    return chr(0x10 + ord(c3) - 65)

init_motor()
# move 
turn_speed = 0.8
speed = 0.9
# for i in range(10):
#     turn_left(turn_speed)
#     time.sleep(0.2)
# for i in range(10):
#     turn_right(turn_speed)
#     time.sleep(0.2)
while True:
    key = readkey()
    if key=='w':
        go_forward(speed)
    elif key=='s':
        go_backward(speed)
    elif key=='d':
        turn_right(turn_speed)
    elif key=='a':
        turn_left(turn_speed)
    elif key=='p':
        break
    print('\r')

# stop
print("stop")
wiringpi.softPwmWrite(1,0)
wiringpi.softPwmWrite(4,0)
wiringpi.softPwmWrite(5,0)
wiringpi.softPwmWrite(6,0)