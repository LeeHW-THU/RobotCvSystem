from tools import Action
from tools import Sona
from keyboard_read import *
import wiringpi
import time

wiringpi.pinMode(10,0) # Pin#10 can be use to read the infrared signal, 0 means read

top_speed = 100
turn_speed = 0.7
sens = 0.3
speed_rate = 0.5
ctrl = Action(top_speed, turn_speed, sens)
ctrl.init_motor()
sona = Sona(28,29)

while(True):
    key = readkey()
    if(key=='p'):
        ctrl.stop()
        break
    dist = []
    for i in range(9):
        dist.append(sona.checkdist())
    dist.sort()
        
    print("Dist = ",dist[4])
    if (not wiringpi.digitalRead(10)) or dist[4]<30.0:
        ctrl.go_backward(speed_rate)
        ctrl.turn_right()
    else: 
        ctrl.go_forward(speed_rate)
    ctrl.stop()
