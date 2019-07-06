import zmq
import json
import multiprocessing
import pathlib
import time

class CentralControl():
    def __init__(self):
        #Endpoint for integration
        self.endpoint_map_cc = 'ipc:///run/toponavi/Map/CentralControl.ipc'
        self.endpoint_cc_location = 'ipc:///run/toponavi/CentralControl/Location.ipc'
        self.endpoint_location_cc = 'ipc:///run/toponavi/Location/CentroControl.ipc'
        self.endpoint_cc_executor = 'ipc:///run/toponavi/executor/command.ipc'

        #Create the path
        socket_dir = pathlib.Path('/run/toponavi/CentralControl')
        socket_dir.mkdir(parents=True, exist_ok=True)

        #Socket
        #self.socket_mc =
        #self.socket_cl =
        #self.socket_lc =
        #self.socekt_ce =

        #Address data from input to Map_path
        self.source = 'Room0'
        self.destination = 'Room1'

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


    #Socket for recv the path data
    #--- Module: Map/CentralControl
    #--- Socket: REP/REQ
    #--- Rep Data: multipart ['path', source, destination]
    #--- Req Data: string "dire, destination, ..."
    def client_map_cc(self, context=None):
        context = context or zmq.Context().instance()
        self.socket_mc = context.socket(zmq.REQ)
        self.socket_mc.connect(self.endpoint_map_cc)


    #Socket for send the tmp destination
    #--- Module: CentralControl/Location
    #--- Socket: PUP/SUB
    #--- Pub Data: tar_dest
    def server_cc_location(self, context=None):
        context = context or zmq.Context().instance()
        self.socket_cl = context.socket(zmq.PUB)
        self.socket_cl.bind(self.endpoint_cc_location)


    #Socket for recv the current direction and location
    #--- Module: Location/CentralControl
    #--- Socket: PUP/SUB
    #--- Sub Data: {direcetion:'', location:''}
    def client_location_cc(self, context=None):
        context = context or zmq.Context().instance()
        self.socket_lc = context.socket(zmq.SUB)
        self.socket_lc.connect(self.endpoint_location_cc)
        self.socket_lc.setsockopt(zmq.SUBSCRIBE, b'')   


    #Socket for send the motion data
    #--- Module: CentralControl/Executor
    #--- Socket: DEALER/ROUTRER
    #--- Send Data: multipart ['start/stop/turn', json]
    def server_cc_executor(self, context=None):
        context = context or zmq.Context().instance()
        self.socket_ce = context.socket(zmq.DEALER)
        self.socket_ce.bind(self.endpoint_cc_executor)


    #Navigation
    def navigation(self):
        #Recv the path data from Map
        self.socket_mc.send_multipart([b'path', self.source.encode(), self.destination.encode()] ) 
        recv_data = self.socket_mc.recv_json()
        self.path_data = recv_data['path']
        print('path_data:', self.path_data)
        self.set_target_data()  #Set the first tmp target destination

        while True:
            #Send the tar_dest to Location
            self.socket_cl.send_string(str(self.tar_dest))
            print('send tar_dest:', self.tar_dest)

            #Recv the loc_data from Location
            loc_data = json.loads(self.socket_lc.recv())
            print('loc_data:', loc_data)
            self.cur_dire = loc_data['direction']
            self.cur_location = loc_data['location'] 

            #Navigate
            if self.tar_dest == '##':                               #Path_data is empty
                print('Navigation finish.')
                break
            else:
                if self.tar_dire != 1 and self.tar_dire != -1:   #Need to turn
                    self.set_executor_angle(self.tar_dire * -3.14 / 180)
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
            print(self.executor_status)

            #Send the data to executor
            if self.executor_status == 1:
                self.socket_ce.send_multipart([b'start', b'none'])
            elif self.executor_status == 2:
                self.socket_ce.send_multipart([b'stop', b'none'])
            elif self.executor_status == 3:
                self.socket_ce.send_multipart([b'turn', self.executor_angle.encode()])
            else:
                self.socket_ce.send_multipart([b'stop', b'none'])
            


    #Run the server and client             
    def run(self):
        #Get the address
        #self.input_address()  

        #Create sockets
        self.client_map_cc()
        self.server_cc_location()
        self.client_location_cc()
        self.server_cc_executor()
        
        #Start navigation
        toponavi = multiprocessing.Process(target=self.navigation)
        toponavi.start()
        toponavi.join()


if __name__ == "__main__":
    central_control = CentralControl()
    central_control.run()
