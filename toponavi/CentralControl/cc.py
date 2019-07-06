import json
import multiprocessing
import threading
import time
import pathlib
import zmq

class CentralControl():
    def __init__(self):
        #Endpoint for integration
        self.endpoint_map_cc = 'ipc:///run/toponavi/Map/CentralControl.ipc'
        self.endpoint_cc_location = 'ipc:///run/toponavi/CentralControl/Location.ipc'
        self.endpoint_location_cc = 'ipc:///run/toponavi/Location/CentroControl.ipc'
        self.endpoint_cc_executor = 'ipc:///run/toponavi/executor/command.ipc'

        socket_dir = pathlib.Path('/run/toponavi/CentralControl')
        socket_dir.mkdir(parents=True, exist_ok=True)

        #Endpoint for test
        self.test1_endpoint = 'ipc:///tmp/1.ipc'
        self.test2_endpoint = 'ipc:///tmp/2.ipc'
        self.test3_endpoint = 'ipc:///tmp/3.ipc'
        self.test4_endpoint = 'ipc:///tmp/4.ipc'

        #Address data from input to Map_path
        self.source = 'Room1'
        self.destination = 'Room2'

        #Path data from Map_path
        self.path_data = []

        #Temp target location data from path_data to Navigation
        #--- Target direction: diricetion(1/-1) or angle
        #--- Target destination: marker_id
        self.tar_dire = 1
        self.tar_dest = 0

        #Current direction and location data
        #--- Current direction: 1/-1
        #--- Current status: 'arr'/'nar'
        self.cur_dire = 1
        self.cur_location = 'nar'

        #Motion data from Navigation to Executor
        #--- Motion status: start, stop, turn
        #--- Angle data: radian
        self.executor_status = 0
        self.executor_angle = json.dumps({'angle': 0})


    #Set the address from input
    def set_address(self, source, destination):
        self.source = source
        self.destination = destination


    #Set the temp target location data from Map_path
    def set_target_data(self):
        if (len(self.path_data) != 0):
            self.tar_dire = self.path_data[0]
            self.tar_dest = self.path_data[1]
            self.path_data.pop(0)
            self.path_data.pop(0)
        else:
            self.tar_dire = 1
            self.tar_dest = 999


    #Set the motion status and motion angle to executor
    def set_executor_status(self, executor_status):
        self.executor_status = executor_status

    def set_executor_angle(self, executor_angle):
        angle_data = {'angle': executor_angle}
        self.executor_angle = json.dumps(angle_data)


    #Get the input address
    def input_address(self):
        source = input("Input the source >>> ")
        destination = input("Input the destination >>> ")
        self.set_address(source, destination)


    #Recv the path data
    #--- Module: Map/CentralControl
    #--- Socket: REP/REQ
    #--- Rep Data: multipart ['path', source, destination]
    #--- Req Data: string "dire, destination, ..."
    def client_map_cc(self, endpoint, context=None):
        context = context or zmq.Context().instance()
        socket = context.socket(zmq.REQ)
        socket.connect(endpoint)

        socket.send_multipart([b'path', self.source.encode(), self.destination.encode()] )
        recv_data = socket.recv_json()
        self.path_data = recv_data['path']
        print('path_data: ', self.path_data)
        self.set_target_data()  #Set the first tmp target destination


    #Send the tmp destination
    #--- Module: CentralControl/Location
    #--- Socket: PUP/SUB
    #--- Pub Data: tar_dest
    def server_cc_location(self, endpoint, context=None):
        context = context or zmq.Context().instance()
        socket = context.socket(zmq.PUB)
        socket.bind(endpoint)
        while True:
            socket.send_string(str(self.tar_dest))
            print('tar_dest: {}'.format(self.tar_dest))
            time.sleep(3)


    #Recv the current direction and location
    #--- Module: Location/CentralControl
    #--- Socket: PUP/SUB
    #--- Sub Data: {direcetion:'', location:''}
    def client_location_cc(self, endpoint, context=None):
        context = context or zmq.Context().instance()
        socket = context.socket(zmq.SUB)
        socket.connect(endpoint)
        socket.setsockopt(zmq.SUBSCRIBE, b'')
        while True:
            loc_data = json.loads(socket.recv())
            print('loc_data:' + loc_data)
            self.cur_dire = loc_data['direction']
            self.cur_location = loc_data['location']
            time.sleep(3)


    #Send the motion data
    #--- Module: CentralControl/Executor
    #--- Socket: DEALER/ROUTRER
    #--- Send Data: multipart ['start/stop/turn', json]
    def server_cc_executor(self, endpoint, context=None):
        context = context or zmq.Context().instance()
        socket = context.socket(zmq.DEALER)
        socket.connect(endpoint)
        while True:
            print('CC executor_status: ', self.executor_status)
            if self.executor_status == 1:
                socket.send_multipart([b'start', b'none'])
            elif self.executor_status == 2:
                socket.send_multipart([b'stop', b'none'])
            elif self.executor_status == 3:
                socket.send_multipart([b'turn', self.executor_angle.encode()])
            else:
                socket.send_multipart([b'stop', b'none'])
            time.sleep(3)


    #Navigation
    def navigation(self):
        while True:
            if self.tar_dest == '##':                               #Path_data is empty
                print('Navigation finish.')
                break
            else:
                if self.tar_dire != 1 and self.tar_dire != -1:   #Need to turn
                    self.set_executor_angle(self.tar_dire * 3.14 / 180)
                    self.set_executor_status(3)                     #turn
                else:
                    if self.cur_dire != self.tar_dire:              #The current dircetion is opposite
                        self.set_executor_angle(3.14)
                        self.set_executor_status(3)                 #turn
                    else:
                        if self.cur_location == 'nar':              #Not arrive the target marker
                            self.set_executor_status(1)             #start
                        elif self.cur_location == 'arr':            #Arrive the target marker
                            self.set_executor_status(2)             #stop
                            self.set_target_data()                  #Update the tmp target
                        else:
                            self.set_executor_status(2)             #stop
            time.sleep(3)


    #Run the server and client
    def run(self):
        # client_mc = multiprocessing.Process(target=self.client_map_cc, args=(self.endpoint_map_cc,))
        # server_cl = multiprocessing.Process(target=self.server_cc_location, args=(self.endpoint_cc_location,))
        # client_lc = multiprocessing.Process(target=self.client_location_cc, args=(self.endpoint_location_cc,))
        # server_ce = multiprocessing.Process(target=self.server_cc_executor, args=(self.endpoint_cc_executor,))

        client_mc = threading.Thread(target=self.client_map_cc, args=(self.endpoint_map_cc,))
        server_cl = threading.Thread(target=self.server_cc_location, args=(self.endpoint_cc_location,))
        client_lc = threading.Thread(target=self.client_location_cc, args=(self.endpoint_location_cc,))
        server_ce = threading.Thread(target=self.server_cc_executor, args=(self.endpoint_cc_executor,))

        toponavi = threading.Thread(target=self.navigation)

        #self.input_address()    #Get the address
        client_mc.start()       #Req the path data
        server_cl.start()       #Send the tmp target data
        client_lc.start()       #Recv the location data
        server_ce.start()       #Send the motion data

        toponavi.start()        #Start navigation


if __name__ == "__main__":
    central_control = CentralControl()
    central_control.run()