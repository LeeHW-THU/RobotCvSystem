import zmq
import json
import threading
import time
import pathlib

class Location():
    def __init__(self):
        self.mark_endpoint = 'ipc:///run/toponavi/MarkerDetector/Location.ipc'
        self.cc_endpoint = 'ipc:///run/toponavi/CentralControl/Location.ipc'
        self.loc_endpoint = 'ipc:///run/toponavi/Location/CentralControl.ipc'

        self.test2 = 'ipc:///tmp/2.ipc'
        self.test3 = 'ipc:///tmp/3.ipc'
        self.marker_data = {}
        self.localmark = None
        self.direction = None
        self.location = ''


    def set_direction(self):
        if len(self.marker_data["euAngles"]):
            if(self.marker_data["euAngles"][0][0]<=175 and self.marker_data["euAngles"][0][0]>=120):
                self.direction = 1
            if(self.marker_data["euAngles"][0][0]<=-120 and self.marker_data["euAngles"][0][0]>=-175):
                self.direction = -1


    def set_Location(self):
        m = None
        for i in range(len(self.marker_data["ids"])):
            if(self.marker_data["ids"][i][0]==self.localmark):
                m = i
                if self.marker_data["dists"][m][0]>20 :
                    self.location = 'nar'
                else:
                    self.location = 'arr'
        if m is None :
            self.location = 'nar'


    def marker_location_client(self, endpoint):
        context = zmq.Context.instance()
        socket = context.socket(zmq.SUB)
        socket.connect(endpoint)
        socket.setsockopt(zmq.SUBSCRIBE, b'')
        f = open("result.json","w")
        while True:
            self.direction = None
            data = socket.recv_json()
            json.dump(data, f)
            self.marker_data = data
            # time.sleep(3)
            print(self.marker_data["dists"])
            print("localmark", self.localmark)
            if (self.marker_data) and (self.localmark is not None) :
                self.set_direction()
                self.set_Location()
            print(self.direction)

    def cc_location_client(self, endpoint):
        context = zmq.Context.instance()
        socket = context.socket(zmq.SUB)
        socket.setsockopt(zmq.SUBSCRIBE, b'')
        socket.connect(endpoint)
        while True:
            data = socket.recv_string()
            print('location recieved: ', data)
            self.localmark = int(data)
            # time.sleep(3)

    def cc_location_server(self, endpoint):
        context = zmq.Context.instance()
        socket = context.socket(zmq.PUB)
        socket.bind(endpoint)
        while True:
            location_date={"direction":self.direction,"location":self.location}
            data = json.dumps(location_date)
            socket.send(data.encode())
            print('location_date sent')
            time.sleep(1)

    def run(self):
        ml_client = threading.Thread(target = self.marker_location_client, args=(self.mark_endpoint,))
        cl_client = threading.Thread(target = self.cc_location_client, args=(self.cc_endpoint,))
        # cl_server = threading.Thread(target = self.cc_location_server, args=(self.test3,))
        cl_server = threading.Thread(target = self.cc_location_server, args=(self.loc_endpoint,))
        # cl_client = threading.Thread(target = self.cc_location_client, args=(self.test2,))
        cl_client.start()
        ml_client.start()
        cl_server.start()

if __name__ == "__main__":
    socket_dir = pathlib.Path("/run/toponavi/Location")
    socket_dir.mkdir(parents=True, exist_ok=True)

    location_test = Location()
    location_test.run()
