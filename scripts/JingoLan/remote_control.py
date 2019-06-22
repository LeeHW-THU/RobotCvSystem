# from motion import *
from tools import Action
# read key
from keyboard_read import *
import wiringpi

if __name__ == "__main__":
    # move 
    top_speed = 100
    turn_speed = 0.5
    sens = 0.3
    speed_rate = 0.5
    ctrl = Action(top_speed, turn_speed, sens)
    ctrl.init_motor()
    while True:
        key = readkey()
        if key=='w':
            ctrl.go_forward(speed_rate)
        elif key=='s':
            ctrl.go_backward(speed_rate)
        elif key=='d':
            ctrl.turn_right()
        elif key=='a':
            ctrl.turn_left()
        elif key=='p':
            break

    # stop
    print("stop")
    ctrl.stop()
    