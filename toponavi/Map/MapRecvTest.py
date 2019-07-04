import zmq
import multiprocessing
import json

def outTest():
    ctx = zmq.Context()
    reqSocket = ctx.socket(zmq.REQ)
    # reqSocket.setsockopt(zmq.REQ)
    reqSocket.connect("ipc:///run/toponavi/Map/CentralControl.ipc")
    staName = "Room1"
    desName = "Room5"
    reqSocket.send_multipart([b'path',staName.encode(), desName.encode()])
    f = open("result.json","w")
    while True:
        result = reqSocket.recv_json()
        json.dump(result, f)
        print(result)
        break
    pass

if __name__ == "__main__":
    process = multiprocessing.Process(target=outTest)
    process.start()
    pass