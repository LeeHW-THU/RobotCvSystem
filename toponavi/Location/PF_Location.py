import zmq
import json
import multiprocessing
import time
import pathlib
import numpy as np
import scipy.stats
from numpy.random import uniform, randn, random

class PF_Location():
    def __init__(self):
        self.mark_endpoint = 'ipc:///run/toponavi/MarkerDetector/Location.ipc'
        self.cc_endpoint = 'ipc:///run/toponavi/CentralControl/Location.ipc'
        self.loc_endpoint = 'ipc:///run/toponavi/Location/CentralControl.ipc'
        self.map_endpoint = 'ipc:///run/toponavi/Map/Location.ipc'

        self.test2 = 'ipc:///tmp/2.ipc'
        self.test3 = 'ipc:///tmp/3.ipc'
        
        socket_dir = pathlib.Path("/run/toponavi/Location")
        socket_dir.mkdir(parents=True, exist_ok=True)
        self.marker_data = {}
        self.iddata = {}
        self.time1 = 0.
        self.time2 = None
        self.timedata = {}
        self.localmark = None
        self.direction = None
        self.mapinfor = {}
        self.maploc=None
        self.location = ''
        self.mu = 0

    def create_uniform_particles(self, x_range, N):
        particles = np.random.rand(N)*x_range
        return particles

    def predict(self, particles, u, std, dt, dir):
        N = len(particles)
        particles += u*dt*dir + (randn(N) * std) 


    def update(self,particles, weights, z, R, landmarks):
        weights.fill(1.)
        for i, landmark in enumerate(landmarks):
            distance = abs(particles - landmark)
            weights *= scipy.stats.norm(distance, R).pdf(z[i])

        weights += 1.e-300  # avoid round-off to zero
        weights /= sum(weights)  # normalize


    def estimate(self,particles, weights):
        pos = particles
        mean = np.average(pos, weights=weights, axis=0)
        var = np.average((pos - mean) ** 2, weights=weights, axis=0)
        return mean, var


    def neff(self,weights):
        return 1. / np.sum(np.square(weights))


    def simple_resample(self,particles, weights):
        N = len(particles)
        cumulative_sum = np.cumsum(weights)
        cumulative_sum[-1] = 1.  # avoid round-off error
        indexes = np.searchsorted(cumulative_sum, random(N))

        # resample according to indexes
        particles[:] = particles[indexes]
        weights[:] = weights[indexes]
        weights /= np.sum(weights)  # normalize




    def set_direction(self):
        if len(self.marker_data["euAngles"]):
            if(self.marker_data["euAngles"][0][0]<=175 and self.marker_data["euAngles"][0][0]>=95):
                self.direction = 1
            if(self.marker_data["euAngles"][0][0]<=-95 and self.marker_data["euAngles"][0][0]>=-175):
                self.direction = -1


    def set_Location(self):
        for j in range(len(self.mapinfor["mkList"]["id"])):
            if self.mapinfor["mkList"]["id"][j] == self.localmark :
               n = j
               if self.mu >= self.mapinfor["mkList"]["dist"][n] :
                  self.location ='arr'                  
        else:
           self.location = 'nar'


    def create_socket(self, context=None):
        context = zmq.Context().instance()
        self.socket_cl1 = context.socket(zmq.SUB)
#        self.socket_cl1.connect(self.test3)            # test
        self.socket_cl1.connect(self.cc_endpoint)
        self.socket_cl1.setsockopt(zmq.SUBSCRIBE, b'')

        context = zmq.Context().instance()
        self.socket_cl2 = context.socket(zmq.SUB)
        self.socket_cl2.connect(self.test2)           #test
#        self.socket_cl1.connect(self.cc_endpoint)
        self.socket_cl2.setsockopt(zmq.SUBSCRIBE, b'')

        context = zmq.Context().instance()
        self.socket_ml = context.socket(zmq.REQ)
        self.socket_ml.connect(self.map_endpoint)

        context = zmq.Context().instance()
        self.socket_lc = context.socket(zmq.PUB)
        self.socket_lc.bind(self.loc_endpoint)

        context = zmq.Context().instance()
        self.socket_marl = context.socket(zmq.SUB)
        self.socket_marl.connect(self.mark_endpoint)
        self.socket_marl.setsockopt(zmq.SUBSCRIBE, b'')


    def PFrun(self, N = 5000, sensor_std_err = 0.1):
        while True:
        #   cc to loc
            print("a")            
            self.iddata = self.socket_cl1.recv_json()
            print(len(self.iddata["tar_dest"]))
            self.localmark = self.iddata["tar_dest"][0]


            while len(self.iddata["tar_dest"]) == 0 :
                self.iddata = self.socket_cl1.recv_json() 
                self.localmark = self.iddata["tar_dest"][0]
            print('location recieved: ', self.localmark)
        #   loc to map and map to loc
            mapmark = {"id":self.localmark}
            self.socket_ml.send_json(mapmark)
            self.mapinfor = self.socket_ml.recv_json()
            max = self.mapinfor["mkList"]["dist"][-1]
            particles = self.create_uniform_particles(max, N) ## max的值，需要具体接口知道实际地图的大小
            weights = np.zeros(N)
            landmarks =[]
            targetID =None
            while self.mu <= max :
                #   mark  to  loc
                nowid = None
                count = 0
                while len(self.marker_data["dists"]) == 0 and count < 10:
                   self.marker_data = self.socket_marl.recv_json()
                   count += 1
                   
                print(self.marker_data["dists"])
                print("localmark", self.localmark)
                if (self.marker_data) and (self.localmark is not None) :
                    self.set_direction() 
                    targetID2 = targetID
                    targetID = self.marker_data["ids"][0][0]
                    m = None
                    for i in range(len(self.marker_data["ids"])) :
                        if(self.marker_data["ids"][i][0]==self.localmark):
                           nowid = self.localmark
                           m = i
                           for j in range(len(self.mapinfor["mkList"]["id"])):
                               if self.mapinfor["mkList"]["id"][j] == self.localmark :                             
                                   marklocal=self.mapinfor["mkList"]["dist"][j]
                                   landmarks.append(marklocal)
                    if m is None:
                        if(targetID2 != targetID):
                            if(len(landmarks)):
                                landmarks.pop()
                            for j in range(len(self.mapinfor["mkList"]["id"])):
                                if self.mapinfor["mkList"]["id"][j] == targetID :
                                    s = j
                            marklocal=self.mapinfor["mkList"]["dist"][s]
                            landmarks.append(marklocal)
                            nowid=targetID
                    print("Now TGmark is %s"%(nowid))
                    print(self.direction)
                xs = []
                #   设置时间：
                self.time2 = self.time1
                while len(self.iddata["time"]) == 0 :
                    self.timedata = self.socket_cl2.recv_json() 
                    self.time1 = self.iddata["time"][0]
                time = self.time1 - self.time2
                dire = self.direction
                if dire is not None:                
                    self.predict(particles, u=51, std = 0.2, dt = time,dir = dire) ##单位厘米 51厘米每秒
                if dire is None:
                    self.predict(particles, u=51, std = 0.2, dt = time,dir = 1)
                if(len(landmarks)):
                    if m is not None :
                       ds = self.marker_data["dists"][m][0]
                    else:
                       ds = self.marker_data["dists"][0][0]
                    self.update(particles, weights, z=ds, R=sensor_std_err, landmarks=landmarks)##更新粒子权值
                if self.neff(weights) < N / 2 :##判断是否需要重采样
                   self.simple_resample(particles, weights)
                self.mu, self.var = self.estimate(particles, weights)
                xs.append(self.mu)
                print("Get the current car position as follows : %s" %self.mu)
                self.set_Location()  
#               传输部分：
                location_date={"direction":self.direction,"location":self.location}
                self.socket_lc.send(location_date)
                self.direction = None
                # time.sleep(3)
    def run(self) :
        self.create_socket()
        self.PFrun()

if __name__ == "__main__":
    location_test = PF_Location()
    location_test.run()
