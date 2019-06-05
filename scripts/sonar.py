#!/usr/bin/python
import wiringpi
import time

def checkdist():
    wiringpi.digitalWrite(28, 0)
    time.sleep(0.000015)
    wiringpi.digitalWrite(28, 1)
    t0=time.time()
    while not wiringpi.digitalRead(29):
        t=time.time()
        if (t-t0)>0.1:
            break
    t1=time.time()
    while wiringpi.digitalRead(29):
        t=time.time()
        if (t-t0)>0.1:
            break
    t2=time.time()
    return (t2-t1)*34000/2

wiringpi.wiringPiSetup()
wiringpi.pinMode(28,1) # trigger
wiringpi.pinMode(29,0) # echo

print("Sonar demo")
while True:
    print(round(checkdist(),1))
    time.sleep(0.3)
