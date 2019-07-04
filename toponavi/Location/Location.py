import zmq 
import json 
import multiprocessing 
import time 

class Location():
    def __init__(self):
        self.location_endpoint = 'ipc:///run/toponavi/Map/Location.ipc'
        self.map_endpoint = 'ipc:///run/toponavi/MarkerDetector/Location.ipc'
        self.cc_endpoint = ''
        self.marker_data = {}
        self.localmark = {}
        self.direction = ''
        self.location = ''


    def set_direction(self):
        if(self.marker_data["euAngles"][0,0]<=180 and self.marker_data["euAngles"][0，0]>=0):
           self.direction = '-'
        else:
           self.direction = '+'


    def set_Location():
        m = 0
        for i in range(len(self.marker_data["ids"][0,:])):
            if(self.marker_data["ids"][0,i]==self.localmark[0]):
                m = i
        if self.marker_data["dists"][0，i]>20 :
           self.location = 'nar'
        else:
           self.location = 'arr'


    def marker_location_client(self, endpoint):
        context = zmq.Context().instance()
        socket = context.socket(zmq.SUB)
        socket.connect(endpoint)
        socket.setsockopt(zmq.SUBSCRIBE, b'')
        while True:
            data = socket.recv().decode()
            self.marker_data = json.loads(data)
            time.sleep(5)
            self.set_direction()
            self.set_Location()

    def cc_location_client(self, endpoint):
        context = zmq.Context().instance()
        socket = context.socket(zmq.SUB)
        socket.connect(endpoint)
        socket.setsockopt(zmq.SUBSCRIBE, b'')
        while True:
            data = socket.recv().decode()
            self.localmark = json.loads(data)
            time.sleep(5)

    def cc_location_server(self, endpoint):
        context = zmq.Context().instance()
        socket = context.socket(zmq.PUB)
        socket.bind(endpoint)
        while True:
            location_date={"direction":self.direction,"location":self.location}
            data = json.dumps(location_date)
            self.socket.send(data.encode())

    def run(self):
        ml_client = multiprocessing.Process(target=map_location_client, args=(self.location_endpoint, ))
        cl_client = multiprocessing.Process(target=cc_location_client, args=(self.map_endpoint,))
        cl_server = multiprocessing.Process(target=cc_location_server,args=(self.location_endpoint,))
        cl_client.start()
        ml_client.start()
        cl_server.start()
