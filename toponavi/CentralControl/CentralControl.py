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
        self.endpoint_location_cc = 'ipc:///run/toponavi/Location/CentralControl.ipc'
        self.endpoint_cc_executor = 'ipc:///run/toponavi/executor/command.ipc'

        #Create the path
        socket_dir = pathlib.Path('/run/toponavi/CentralControl')
        socket_dir.mkdir(parents=True, exist_ok=True)

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

        #Time data to Location
        self.start_time = 0

        #Current direction and location data
        #--- Current direction: 1/-1/None
        #--- Current status: 'arr'/'nar'
        self.cur_dire = 1
        self.cur_location = 'nar'

        #Motion data from Navigation to Executor
        #--- Motion status: start, stop, turn
        #--- Angle data: radian
        self.executor_status = 0
        self.executor_angle = json.dumps({'angle': 0})

        #Current motion data
        self.cur_status = 999
        self.cur_angle = json.dumps({'angle': 9})


    def set_address(self, source, destination):
        '''Set the address from input'''
        self.source = source
        self.destination = destination


    def set_target_data(self):
        '''Set the temp target location data from Map_path'''
        if (len(self.path_data) != 0):
            self.tar_dire = self.path_data[0]
            self.tar_dest = self.path_data[1]
            self.path_data.pop(0)
            self.path_data.pop(0)
        else:
            self.tar_dire = 1
            self.tar_dest = 999


    def reset_start_time(self):
        '''Reset the start_time for Location'''
        self.start_time = time.clock()


    def set_executor_status(self, executor_status):
        '''Set the motion status to executor'''
        self.executor_status = executor_status

    def set_executor_angle(self, executor_angle):
        '''Set the motion angle to executor'''        
        angle_data = {'angle': executor_angle}
        self.executor_angle = json.dumps(angle_data)


    def input_address(self):
        '''Get the input address from keyboard'''        
        source = input("Input the source >>> ")
        destination = input("Input the destination >>> ")
        self.set_address(source, destination)


    def create_socket(self, context=None):
        '''
        Create the socket
        - Map/CC
        - CC/Location
        - Location/CC
        - CC/Executor
        '''

        #Socket for recv the path data
        context = context or zmq.Context.instance()
        self.socket_mc = context.socket(zmq.REQ)
        self.socket_mc.connect(self.endpoint_map_cc)

        #Socket for send the tmp destination
        context = context or zmq.Context.instance()
        self.socket_cl = context.socket(zmq.PUB)
        self.socket_cl.bind(self.endpoint_cc_location)

        #Socket for recv the current direction and location
        context = context or zmq.Context.instance()
        self.socket_lc = context.socket(zmq.SUB)
        self.socket_lc.setsockopt(zmq.SUBSCRIBE, b'')
        self.socket_lc.connect(self.endpoint_location_cc)

        #Socket for send the motion data
        context = context or zmq.Context.instance()
        self.socket_ce = context.socket(zmq.DEALER)
        self.socket_ce.connect(self.endpoint_cc_executor)


    def recv_path_data(self):
        '''
        Recv the path data from Map
        - Module: Map/CentralControl
        - Socket: REP/REQ
        - Req Data: multipart; ['path', source, destination]
        - Rep Data: json; {"path": [dire, destination, ...]}
        '''
        self.socket_mc.send_multipart([b'path', self.source.encode(), self.destination.encode()] )
        recv_data = self.socket_mc.recv_json()
        self.path_data = recv_data['path']
        print('path_data:', self.path_data)
        self.set_target_data()  #Set the first tmp target destination


    def send_tar_dest(self):
        '''
        Send the tar_dest to Location
        - Module: CentralControl/Location
        - Socket: PUP/SUB
        - Pub Data: json; '{"tar_dest": tar_dest}'
        '''
        data = {'tar_dest': self.tar_dest}
        self.socket_cl.send_json(data)
        print('send tar_dest:', self.tar_dest)

    
    def send_time_difference(self):
        '''
        Send the time to Location
        - Module: CentralControl/Location
        - Socket: PUP/SUB
        - Pub Data:json '{"time": time}'
        '''
        time = time.clock() - self.start_time
        data = {'time': time}
        self.socket_cl.send_json(data)
        print('time:', time)


    def recv_loc_data(self):
        '''
        Recv the loc_data from Location
        - Module: Location/CentralControl
        - Socket: PUP/SUB
        - Sub Data: json; {"direcetion":'', "location":''}        
        '''
        loc_data = self.socket_lc.recv_json()
        print('loc_data:', loc_data)
        self.cur_dire = loc_data['direction']
        self.cur_location = loc_data['location']


    def send_motion_data(self):
        '''
        Send motion data to executor
        - Module: CentralControl/Executor
        - Socket: DEALER/ROUTRER
        - Send Data: multipart ['start/stop/turn', json]        
        '''
        if self.executor_status == 1:
            self.socket_ce.send_multipart([b'start', b'none'])
        elif self.executor_status == 2:
            self.socket_ce.send_multipart([b'stop', b'none'])
        elif self.executor_status == 3:
            self.socket_ce.send_multipart([b'turn', self.executor_angle.encode()])
        else:
            self.socket_ce.send_multipart([b'stop', b'none'])
        print('Send executor data:', self.executor_status)


    def navigation(self):
        '''
        Navigation
        - init
           - Recv the path data from Map
        - loop
           - Send the tar_dest to Location
           - Recv the loc_data from Location
           - Set executor_status
           - Decide if send executor_status to executor
        '''
        #Recv the path data from Map
        self.recv_path_data()
        self.reset_start_time()

        while True:
            #Send the tar_dest to Location
            self.send_tar_dest()

            #Send the time difference
            self.send_time_difference()

            #Recv the loc_data from Location
            self.recv_loc_data()

            #Set executor_status
            if self.tar_dest == '##':                               #Path_data is empty
                print('Navigation finish.')
                break
            else:
                if self.tar_dire != 1 and self.tar_dire != -1:      #Need to turn
                    self.set_executor_angle(self.tar_dire * 3.14 / 180)
                    self.set_executor_status(3)                     #turn
                else:
                    if self.cur_dire is None:
                        self.set_executor_status(1)
                    elif self.cur_dire != self.tar_dire:            #The current dircetion is opposite
                        self.set_executor_angle(3.14)
                        self.set_executor_status(3)                 #turn
                    else:
                        if self.cur_location == 'nar':              #Not arrive the target marker
                            self.set_executor_status(1)             #start
                        elif self.cur_location == 'arr':            #Arrive the target marker
                            #self.set_executor_status(2)            
                            self.set_target_data()                  #Update the tmp target
                        else:
                            self.set_executor_status(2)             #stop
            print('Set executor_status: ', self.executor_status)

            #Decide if send executor_status to executor
            if self.cur_status != 3:                                                                #Befor turn
                if self.cur_status != self.executor_status:                                         #Send motion data to executor
                    self.send_motion_data()
                    self.cur_status = self.executor_status
                    self.cur_angle = self.executor_angle
                    self.reset_start_time()
                    print('Send exector_status', self.executor_status)
                else:                                                                               #Same status, do not send
                    print('Do not send exector status because of same status')
            else:                                                                                   #After turn
                if self.executor_status == 1:                                                       #When it is turning, do not send start
                    print('Do not send exector status because of turning')
                elif self.executor_status == 3 and self.cur_angle == self.executor_angle:           #Same turning, do not send
                    print('Do not send exector status because of same turning')
                else:                                                                               #Different turning or stop, send motion data
                    self.send_motion_data()
                    self.cur_status = self.executor_status
                    self.cur_angle = self.executor_angle
                    self.reset_start_time()
                    if self.executor_angle['angle'] != 3.14:
                        print('Send exector_status', self.executor_status)


    def run(self):
        #Get the address
        #self.input_address()

        #Create sockets
        self.create_socket()

        #Start navigation
        self.navigation()


if __name__ == "__main__":
    central_control = CentralControl()
    central_control.run()
