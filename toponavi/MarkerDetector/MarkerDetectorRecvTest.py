import zmq
import multiprocessing
import json

def outTest():
    ctx = zmq.Context()
    dataSocket = ctx.socket(zmq.SUB)
    dataSocket.setsockopt(zmq.SUBSCRIBE, b'')
    dataSocket.connect("ipc:///run/toponavi/MarkerDetector/Location.ipc")
    f = open("result.json","w")
    while True:
        result = dataSocket.recv_json()
        json.dump(result, f)
        print(result)
        # break
    pass

if __name__ == "__main__":
    process = multiprocessing.Process(target=outTest)
    process.start()
    pass