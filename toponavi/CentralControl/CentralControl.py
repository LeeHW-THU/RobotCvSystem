import zmq
import json
import multiprocessing
import time

class CentralControl():
    def __init__(self):
        self.executor_endpoint = 'ipc:///run/toponavi/executor/command.ipc'
        self.location_endpoint = 'ipc:///run/toponavi/Map/Location.ipc'
        self.map_endpoint = 'ipc:///run/toponavi/Map/CentralControl.ipc'
        
        self.test1_endpoint = 'ipc:///tmp/1.ipc'
        self.test2_endpoint = 'ipc:///tmp/2.ipc'
        self.test3_endpoint = 'ipc:///tmp/3.ipc'
        self.test4_endpoint = 'ipc:///tmp/4.ipc'
        
        self.executor_status = 0
        self.executor_angle = '{}'
        
        self.source = 'room 0'
        self.destination = 'room 1'
        
        self.path_data = []
        self.cur_loc_info = '0'
        self.cur_dest = '0'
        
    def set_executor_status(self, executor_status):
        self.executor_status = executor_status
        
    def set_executor_angle(self, executor_angle):
        angle_data = {'angle': executor_angle}
        self.executor_angle = json.dumps(angle_data)
        
    def set_current_destnation(self):
        if (len(self.path_data) != 0):
            self.cur_loc_info = self.path_data[0]
            self.cur_dest = self.path_data[1]
        else:
            self.cur_loc_info = '0'
            self.cur_dest = '0'
    
    def executor_server(self, endpoint, context=None):
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
            print('data send')
            time.sleep(5)
    
    def map_client(self, endpoint, context=None):
        context = context or zmq.Context().instance()
        socket = context.socket(zmq.REQ)
        socket.connect(endpoint)
        
        socket.send_multipart([b'path', self.source.encode(), self.destination.encode()] ) 
        self.path_data = socket.recv().split()
    
    def location_client(self, endpoint, context=None):
        context = context or zmq.Context().instance()
        socket = context.socket(zmq.SUB)
        socket.connect(endpoint)
        socket.setsockopt(zmq.SUBSCRIBE, b'')
        while True:
            loc_data = json.loads(socket.recv())
            print(loc_data)
            direction = loc_data['direction']
            location = loc_data['location']
            
            if location == 'nar':
                self.set_executor_status(1)
            else:
                self.set_executor_status(2)
                
            time.sleep(5)
            
    def location_server(self, endpoint, context=None):
        context = context or zmq.Context().instance()
        socket = context.socket(zmq.PUB)
        socket.bind(endpoint)
        while True: 
            socket.send(self.cur_dest.encode())
            
    def run(self):
        #executor_server = multiprocessing.Process(target=self.executor_server, args=(self.executor_endpoint,))
        #location_client = multiprocessing.Process(target=self.location_client, args=(self.location_endpoint,))
        
        executor_server = multiprocessing.Process(target=self.executor_server, args=(self.test1_endpoint,))
        location_client = multiprocessing.Process(target=self.location_client, args=(self.test2_endpoint,))
        
        executor_server.start()
        location_client.start()

if __name__ == "__main__":
    central_control = CentralControl()
    central_control.run()
