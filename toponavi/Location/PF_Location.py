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
        self.iddata = None
        self.time1 = 0.
        self.time2 = None
        self.timedata = None
        self.localmark = None
        self.direction = None
        self.mapinfor = {}
        self.maploc=None
        self.location = ''
        self.mu = 0

    # 创建粒子
    def create_uniform_particles(self, x_range, N):
        particles = np.random.rand(N)*x_range
        return particles
    # 状态转化器
    def predict(self, particles, u, std, dt, dir):
        N = len(particles)
        particles += u*dt*dir + (randn(N) * std)

    #更新粒子权值
    def update(self,particles, weights, z, R, landmarks):
        weights.fill(1.)
        for i, landmark in enumerate(landmarks):
            distance = abs(particles - landmark)
            weights *= scipy.stats.norm(distance, R).pdf(z[i])

        weights += 1.e-300  # avoid round-off to zero
        weights /= sum(weights)  # normalize

 #  加权平均求预计位置
    def estimate(self,particles, weights):
        pos = particles
        mean = np.average(pos, weights=weights, axis=0)
        var = np.average((pos - mean) ** 2, weights=weights, axis=0)
        return mean, var

#   判断是否进行重采样的条件
    def neff(self,weights):
        return 1. / np.sum(np.square(weights))

# 重采样
    def simple_resample(self,particles, weights):
        N = len(particles)
        cumulative_sum = np.cumsum(weights)
        cumulative_sum[-1] = 1.  # avoid round-off error
        indexes = np.searchsorted(cumulative_sum, random(N))

        # resample according to indexes
        particles[:] = particles[indexes]
        weights[:] = weights[indexes]
        weights /= np.sum(weights)  # normalize



#   确定小车运动方向
    def set_direction(self):
        if len(self.marker_data["euAngles"]):
            if(self.marker_data["euAngles"][0][0]<=175 and self.marker_data["euAngles"][0][0]>=95):
                self.direction = 1
            if(self.marker_data["euAngles"][0][0]<=-95 and self.marker_data["euAngles"][0][0]>=-175):
                self.direction = -1

#   评估小车位置
    def set_Location(self):
        count = 0
        for j in range(len(self.mapinfor["mkList"])):
            if self.mapinfor["mkList"][j]["id"] == self.localmark :
                n = j
                print("find")
                if self.mu > self.mapinfor["mkList"][n]["dist"]*100  :
                    self.location = 'arr'
                    count = 1
        if self.location = 'arr' and count == 1 :
            self.location = 'nar'
        if count == 0 :
            self.location = 'nar'

#   创建多个socket
    def create_socket(self, context=None):
        context = zmq.Context.instance()
        self.socket_cl = context.socket(zmq.ROUTER)
#        self.socket_cl1.connect(self.test3)            # test
        self.socket_cl.bind(self.loc_endpoint)


        context = zmq.Context.instance()
        self.socket_ml = context.socket(zmq.REQ)
        self.socket_ml.connect(self.map_endpoint)

        context = zmq.Context.instance()
        self.socket_lc = context.socket(zmq.DEALER)
        self.socket_lc.connect(self.cc_endpoint)

        context = zmq.Context.instance()
        self.socket_marl = context.socket(zmq.SUB)
        self.socket_marl.connect(self.mark_endpoint)
        self.socket_marl.setsockopt(zmq.SUBSCRIBE, b'')

#   运行部分，单进程
    def PFrun(self, N = 5000, sensor_std_err = 0.1):
        while True:
        #   cc to loc
            print("begin work")
            topic, data = self.socket_cl.recv_multipart()
            data = data.decode()
            data = json.loads(data)
            self.iddata = data['tar_dest']
            print(self.iddata)
            self.localmark = self.iddata
            print('location recieved: ', self.localmark)

        #   loc to map and map to loc
            mapmark = {"id":self.localmark}
            self.socket_ml.send_json(mapmark)
            self.mapinfor = self.socket_ml.recv_json()
            max = self.mapinfor["mkList"][-1]['dist']*100
            print(max)
            particles = self.create_uniform_particles(max, N) ## max的值，需要具体接口知道实际地图的大小

            weights = np.zeros(N)
            targetID =None
            self.mu = 0
            while self.mu <= max :
                #   mark  to  loc
                landmarks = []
                nowid = None
                count = 1
                self.marker_data = self.socket_marl.recv_json()
                while len(self.marker_data["dists"]) == 0 and count < 10:
                    self.marker_data = self.socket_marl.recv_json()
                    count += 1


                print("localmark", self.localmark)
#               限制条件，需要在有目标mark和小车在看的到mark的情况下进行，如果看不到，粒子无法更新权值 只能移动
                if self.marker_data["ids"] and (self.localmark is not None) :
                    self.set_direction()
                    targetID2 = targetID
                    targetID = self.marker_data["ids"][0][0]
#               判断小车视野里是否有目标mark 如果有，直接锁定目标mark
                    m = None
                    for i in range(len(self.marker_data["ids"])) :
                        if(self.marker_data["ids"][i][0]==self.localmark):
                            nowid = self.localmark
                            m = i

                            for j in range(len(self.mapinfor["mkList"])):
                                if self.mapinfor["mkList"][j]["id"] == self.localmark :
                                    marklocal=self.mapinfor["mkList"][j]["dist"]*100
                                    landmarks.append(marklocal)
#               小车视野里没有目标mark时，就用视野中其它mark作为判定位置的依据
                    if m is None:
                            for j in range(len(self.mapinfor["mkList"])):
                                if self.mapinfor["mkList"][j]["id"] == targetID :
                                    s = j
                                    marklocal=self.mapinfor["mkList"][s]["dist"]*100
                                    landmarks.append(marklocal)
                                    nowid=targetID

                    print("Now TGmark is %s"%(nowid))
                    print(self.direction)
                xs = []
                #   设置时间：
                if  data is None :
                    topic, data = self.socket_cl.recv_multipart()
                    data = data.decode()
                    data = json.loads(data)
                self.time2 = self.time1
                self.timedata = data['time']
                self.time1 = self.timedata
                time = self.time1 - self.time2
                print("time",self.time1)
                data = None
#               状态更新模块
                dire = self.direction
                if dire is not None:
                    self.predict(particles, u=48.5, std = 0.2, dt = time, dir = dire) ##单位厘米 51厘米每秒
                if dire is None:
                    self.predict(particles, u=48.5, std = 0.2, dt = time, dir = 1)

#               权值更新模块
                if(len(landmarks)):
                    if m is not None :
                        ds = self.marker_data["dists"][m][0]
                    else:
                        ds = self.marker_data["dists"][0][0]
                    print(ds)
                    dz = [ds]
                    self.update(particles, weights, z=dz, R=sensor_std_err, landmarks=landmarks)##更新粒子权值

                if (weights == 0).all():
                    weights = np.ones(N) / (N*100)

                if self.neff(weights) < N / 2 :##判断是否需要重采样
                    self.simple_resample(particles, weights)

#               得出预测小车的位置
                self.mu, self.var = self.estimate(particles, weights)
                xs.append(self.mu)
                print("Get the current car position as follows : %s" %self.mu)
                self.set_Location()

#               传输部分：
                location_date={"direction":self.direction,"location":self.location}
                json_data = json.dumps(location_date)
                self.socket_lc.send(json_data.encode())
                print("send infor",location_date)
                self.direction = None
                # time.sleep(3)


    def run(self) :
        self.create_socket()
        self.PFrun()

if __name__ == "__main__":
    location_test = PF_Location()
    location_test.run()
