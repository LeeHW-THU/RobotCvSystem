## 小车自动创建一个以自身为原点，mark为终点的地图，通过遥控控制前进倒退，可以在地图上实现定位。（单位cm）
##控制小车前进后退一次的数据：0.5倍率，time.sleep（0.3）
##测量得前进后退一次的距离大概为7.655cm
##误差参数还未充分调整。
import numpy as np
from numpy.random import uniform, randn, random
from tools import Action
from keyboard_read import *
import wiringpi
import sys
import cv2
import cv2.aruco as aruco
import time
import scipy.stats
import picamera
def create_uniform_particles(x_range, N):
    particles = np.random.rand(N)*x_range
    return particles    

def predict(particles, d, std, opp):
    N = len(particles)
    particles += (d*opp + (randn(N) * std))


def update(particles, weights, z, R, landmarks):
    weights.fill(1.)
    for i, landmark in enumerate(landmarks):
        distance = abs(particles-landmark)
        weights *= scipy.stats.norm(distance, R).pdf(z[i])

    weights += 1.e-300  # avoid round-off to zero
    weights /= sum(weights)  # normalize

def estimate(particles, weights):
    pos = particles
    mean = np.average(pos, weights=weights, axis=0)
    var = np.average((pos - mean) ** 2, weights=weights, axis=0)
    return mean, var


def neff(weights):
    return 1. / np.sum(np.square(weights))



def simple_resample(particles, weights):
    N = len(particles)
    cumulative_sum = np.cumsum(weights)
    cumulative_sum[-1] = 1.  # avoid round-off error
    indexes = np.searchsorted(cumulative_sum, random(N))

    # resample according to indexes
    particles[:] = particles[indexes]
    weights[:] = weights[indexes]
    weights /= np.sum(weights)  # normalize


def run_pf(N, sensor_std_err=0.1):
    mtx = np.array([
    [2946.48, 0, 1980.53],
    [0, 2945.41, 1129.25],
    [0, 0, 1],
    ])
    dist = np.array([0.226317, -1.21478, 0.00170689, -0.000334551, 1.9892])
    camera = picamera.PiCamera()
    width = 1648
    height = 1232
    camera.resolution = (width, height)
    camera.sharpness = 100
    camera.iso = 800
    camera.brightness = 60
    frame = np.empty((width * height * 3), dtype=np.uint8)
    arucoDict = aruco.DICT_6X6_250
    detector = MarkerDetector(mtx, dist, arucoDict, width, height)
    targetID = 1
    direction = 1
    searchScale = 7
    ##以自己的位置为坐标原点，找到mark的坐标位置
    frame = frame.reshape((height, width, 3))
    corners = None
    timer1 = 0
    while corners is None: ##直到摄像头可以看到mark，并得到数据
        camera.capture(frame, use_video_port=True, format='bgr')
        corners = detector.detectMarker(frame, targetID)
        timer1 += 1
        if(timer1 == 10):
            print("can't find mark")
            break
    sideLen = 0.1
    rvec, tvec, _ = aruco.estimatePoseSingleMarkers(corners, sideLen, mtx, dist)
    marklocal = (math.sqrt(math.pow(tvec[0,0,0],2)+math.pow(tvec[0,0,1],2))/1.48)*100 # 1.48系统误差
    landmarks = np.array([marklocal])
    # create particles and weights
    particles = create_uniform_particles(round(marklocal), N)
    weights = np.zeros(N)
    robot_pos = np.array(0.)
    xs = []
    print("Create maps of 0 to %s"%round(marklocal))
    while True:
        key = readkey()
        if key=='p':
            print("stop working")
            break
        if key == 'w': ##x轴坐标下向前运动
            ctrl.go_forward(speed_rate)
            predict(particles, d=7.655, std=0.2,opp =1)
        if key=='s':  ##x轴坐标下向后运动
            ctrl.go_backward(speed_rate)
            predict(particles, d=7.655, std=0.2,opp =-1)
        frame = frame.reshape((height, width, 3))
        corners = None
        timer2 = 0
        while corners is None: ##直到摄像头可以看到mark，并得到数据
            camera.capture(frame, use_video_port=True, format='bgr')
            corners = detector.detectMarker(frame, targetID)
            timer2 +=1
            if(timer2 == 10):
              print("can't find mark")
              break
        sideLen = 0.1
        rvec, tvec, _ = aruco.estimatePoseSingleMarkers(corners, sideLen, mtx, dist)
        dis = (math.sqrt(math.pow(tvec[0,0,0],2)+math.pow(tvec[0,0,1],2))/1.48)*100 # 1.48系统误差
        ds = np.array([dis])
        update(particles, weights, z=ds, R=sensor_std_err, landmarks=landmarks)##更新粒子权值

        if neff(weights) < N / 2:##判断是否需要重采样
           simple_resample(particles, weights)

        mu, var = estimate(particles, weights)
        xs.append(mu)
        print("Get the current car position as follows : %s" %mu)



if __name__ == '__main__':
    top_speed = 100
    turn_speed = 0.5
    sens = 0.3
    speed_rate = 0.5
    ctrl = Action(top_speed, turn_speed, sens)
    ctrl.init_motor()
    sys.path.append("/home/pi/JingoLan/aruco")
    ## sys.path.append("..")
    from MarkerDetector import MarkerDetector
    from tools import Action
    import math
    run_pf(N=5000)
