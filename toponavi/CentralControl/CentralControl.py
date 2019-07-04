import zmq
import json
import multiprocessing
import time

class CentralControl():
    def __init__(self):
        #Endpoint for integration
        self.endpoint_map_cc = 'ipc:///run/toponavi/Map/CentralControl.ipc'
        self.endpoint_cc_location = 'ipc:///run/toponavi/CentralControl/Location.ipc'
        self.endpoint_location_cc = 'ipc:///run/toponavi/Location/CentroControl.ipc'
        self.endpoint_cc_executor = 'ipc:///run/toponavi/executor/command.ipc'
  
        #Endpoint for test
        self.test1_endpoint = 'ipc:///tmp/1.ipc'
        self.test2_endpoint = 'ipc:///tmp/2.ipc'
        self.test3_endpoint = 'ipc:///tmp/3.ipc'
        self.test4_endpoint = 'ipc:///tmp/4.ipc'
        
        #Address data from input to Map_path
        self.source = 'room 0'
        self.destination = 'room 1'

        #Path data from Map_path
        self.path_data = []

        #Temp target location data from path_data to Navigation
        self.tar_dire = '0'
        self.tar_dest = '0'

        #Motion data from Navigation to Executor
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
            self.tar_dire = '0'
            self.tar_dest = '0'


    #Set the motion status and motion angle to executor    
    def set_executor_status(self, executor_status):
        self.executor_status = executor_status
    
    def set_executor_angle(self, executor_angle):
        angle_data = {'angle': executor_angle}
        self.executor_angle = json.dumps(angle_data)


    #Get the input address
    def input_address(self):
        source = input("Input the source:")
        destination = input("Input the destination")
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
        self.path_data = socket.recv().split()
        print(self.path_data)
    
    #Send the tmp destination
    #--- Module: CentralControl/Location
    #--- Socket: PUP/SUB
    #--- Pub Data: tar_dest
    def server_cc_location(self, endpoint, context=None):
        context = context or zmq.Context().instance()
        socket = context.socket(zmq.PUB)
        socket.bind(endpoint)
        while True: 
            socket.send(self.tar_dest.encode())
            print(self.tar_dest)
            time.sleep(5)


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
            self.set_target_data()
            if self.tar_dire != '+' and self.tar_dire != '-':
                self.set_executor_angle(float(self.tar_dire))
                self.set_executor_status(3)
                time.sleep(5)
            
            loc_data = json.loads(socket.recv())
            print(loc_data)
            direction = loc_data['direction']
            location = loc_data['location']
            
            if direction != self.tar_dire:
                self.set_executor_angle(3.14)
                self.set_executor_status(3)
            elif location == 'nar':
                self.set_executor_status(1)
            else:
                self.set_executor_status(2)
                if len(self.path_data) >= 2:
                    self.path_data.pop(0)
                    self.path_data.pop(0)
                else:
                    pass
                    
            time.sleep(5)


    #Send the motion data
    #--- Module: CentralControl/Executor
    #--- Socket: DEALER/ROUTRER
    #--- Send Data: multipart ['start/stop/turn', json]
    def server_cc_executor(self, endpoint, context=None):
        context = context or zmq.Context().instance()
        socket = context.socket(zmq.DEALER)
        socket.bind(endpoint)
        while True:
            if self.executor_status == 1:
                socket.send_multipart([b'start', b'none'])
            elif self.executor_status == 2:
                socket.send_multipart([b'stop', b'none'])
            elif self.executor_status == 3:
                socket.send_multipart([b'turn', self.executor_angle.encode()])
            else:
                socket.send_multipart([b'stop', b'none'])
            time.sleep(5)

    #Run the server and client             
    def run(self):
        #client_mc = multiprocessing.Process(target=self.client_map_cc, args=(self.endpoint_map_cc,))
        #server_cl = multiprocessing.Process(target=self.server_cc_location, args=(self.endpoint_cc_location,))
        #client_lc = multiprocessing.Process(target=self.client_location_cc, args=(self.endpoint_location_cc))
        #server_ce = multiprocessing.Process(target=self.server_cc_executor, args=(self.endpoint_cc_executor,))
        
        client_mc = multiprocessing.Process(target=self.client_map_cc, args=(self.test1_endpoint,))
        server_cl = multiprocessing.Process(target=self.server_cc_location, args=(self.test2_endpoint,))
        client_lc = multiprocessing.Process(target=self.client_location_cc, args=(self.test3_endpoint,))
        server_ce = multiprocessing.Process(target=self.server_cc_executor, args=(self.test4_endpoint,))

        #Get the address
        self.input_address()
        #Req the path data
        client_mc.start()

        server_cl.start()
        client_lc.start()
        server_ce.start()


if __name__ == "__main__":
    central_control = CentralControl()
    central_control.run()
