import zmq
import json
import pathlib

if __name__ == "__main__":
    ctx = zmq.Context()
    reqSocket = ctx.socket(zmq.REQ)
    # reqSocket.setsockopt(zmq.REQ)
    reqSocket.connect("ipc:///run/toponavi/Map/Location.ipc")
    reqDict = {"id":101}
    reqSocket.send_json(reqDict)
    f = open("result.json","w")
    while True:
        result = reqSocket.recv_json()
        print(result)
        break
    pass