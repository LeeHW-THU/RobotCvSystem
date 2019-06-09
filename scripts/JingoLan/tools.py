#!/usr/bin/python
import wiringpi
import time

class Action:
    def __init__(self, top_speed, turn_speed, sens):
        self.top_speed = top_speed
        self.turn_speed = turn_speed
        self.sens = sens
        wiringpi.wiringPiSetup()


    def init_motor(self):
        # init io
        # left motor
        wiringpi.pinMode(1,1)
        wiringpi.softPwmCreate(1,0,int(self.top_speed))
        wiringpi.softPwmWrite(1,0)

        wiringpi.pinMode(4,1)
        wiringpi.softPwmCreate(4,0,int(self.top_speed))
        wiringpi.softPwmWrite(4,0)

        # right motor
        wiringpi.pinMode(5,1)
        wiringpi.softPwmCreate(5,0,int(self.top_speed))
        wiringpi.softPwmWrite(5,0)

        wiringpi.pinMode(6,1)
        wiringpi.softPwmCreate(6,0,int(self.top_speed))
        wiringpi.softPwmWrite(6,0)

    # motor id and direction:
    #   1: left go forward
    #   4: left go backward
    #   5: right go forwad 
    #   6: right go backward
    def stop(self):
        wiringpi.softPwmWrite(1,0)
        wiringpi.softPwmWrite(4,0)
        wiringpi.softPwmWrite(5,0)
        wiringpi.softPwmWrite(6,0)

    def turn_left(self, speed_rate=1.0):
        # print("Turn Speed: ",int(turn_speed*self.top_speed))
        wiringpi.softPwmWrite(4,int(speed_rate*self.turn_speed*self.top_speed))
        wiringpi.softPwmWrite(5,int(speed_rate*self.turn_speed*self.top_speed))
        wiringpi.softPwmWrite(1,0)
        wiringpi.softPwmWrite(6,0)
        time.sleep(self.sens)
        self.stop()

    def turn_right(self, speed_rate=1.0):
        wiringpi.softPwmWrite(4,0)
        wiringpi.softPwmWrite(5,0)
        wiringpi.softPwmWrite(1,int(speed_rate*self.turn_speed*self.top_speed))
        wiringpi.softPwmWrite(6,int(speed_rate*self.turn_speed*self.top_speed))
        time.sleep(self.sens)
        self.stop()

    def go_forward(self, speed_rate=1.0):
        wiringpi.softPwmWrite(4,0)
        wiringpi.softPwmWrite(5,int(speed_rate*self.top_speed))
        wiringpi.softPwmWrite(1,int(speed_rate*self.top_speed))
        wiringpi.softPwmWrite(6,0)
        time.sleep(self.sens)
        self.stop()

    def go_backward(self, speed_rate=1.0):
        wiringpi.softPwmWrite(4,int(speed_rate*self.top_speed))
        wiringpi.softPwmWrite(5,0)
        wiringpi.softPwmWrite(1,0)
        wiringpi.softPwmWrite(6,int(speed_rate*self.top_speed))
        time.sleep(self.sens)
        self.stop()

class Sona:
    def __init__(self, trigger_pin, echo_pin):
        wiringpi.pinMode(trigger_pin,1) # trigger
        wiringpi.pinMode(echo_pin,0) # echo
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin

    def checkdist(self):
        wiringpi.digitalWrite(self.trigger_pin, 0)
        time.sleep(0.000015)
        wiringpi.digitalWrite(self.trigger_pin, 1)
        t0=time.time()
        while not wiringpi.digitalRead(self.echo_pin):
            t=time.time()
            if (t-t0)>0.1:
                break
        t1=time.time()
        while wiringpi.digitalRead(self.echo_pin):
            t=time.time()
            if (t-t0)>0.1:
                break
        t2=time.time()
        return (t2-t1)*34000/2    
