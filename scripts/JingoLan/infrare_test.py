import wiringpi
import time

wiringpi.wiringPiSetup()
wiringpi.pinMode(10,0) # Pin#10 can be use to read the infrared signal, 0 means read

while(True):
    if(wiringpi.digitalRead(10)): print("Clear\r")
    else: print("Blocked\r")
    time.sleep(0.1)