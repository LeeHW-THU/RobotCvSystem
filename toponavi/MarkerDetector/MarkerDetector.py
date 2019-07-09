import zmq
import threading
import multiprocessing
import numpy as np
import math
import time
import cv2
import cv2.aruco as aruco
import json
import picamera
import pathlib

class MarkerDetector():
    def __init__(self, camConfFile):
        self.outSocketPath = "/run/toponavi/MarkerDetector/Location.ipc"

        self.imgEndpoint = "ipc:///run/toponavi/camera/raw.ipc"
        self.cmdEndpoint = "ipc:///run/toponavi/camera/command.ipc"
        self.markerEndpoint = "ipc://"+self.outSocketPath

        socketDir = pathlib.Path(self.outSocketPath).parent
        socketDir.mkdir(parents=True, exist_ok=True)

        with open(camConfFile, "r") as f:
            camPara = json.load(f)
            self.camMat = np.array(camPara["Mat"])
            self.camDist = np.array(camPara["Dist"])
            self.len = 10
            self.w = 1312 # width of frame
            self.h = 976  # heigth of frame
            self.arucoDict = aruco.Dictionary_get(aruco.DICT_6X6_250)
            self.parameters =  aruco.DetectorParameters_create()

    def rvecToEulerAngel(self, rvec):
        rMat = cv2.Rodrigues(rvec[0])[0]

        sy = math.sqrt(rMat[0,0]*rMat[0,0] + rMat[1,0]*rMat[1,0])
        if(sy<1e-6):
            x = math.atan2(rMat[1,2], rMat[1,1])
            y = math.atan2(-rMat[2,0], sy)
            z = 0
        else:
            x = math.atan2(rMat[2,1], rMat[2,2])
            y = math.atan2(-rMat[2,0], sy)
            z = math.atan2(rMat[1,0], rMat[0,0])

        x = x*180/math.pi
        y = y*180/math.pi
        z = z*180/math.pi
        return np.array([x,y,z])

    def detect(self, frame, targetID=None):
        dict = {"ids":[],"dists":[],"euAngles":[]}
        if frame is None:
            return dict
        # frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        # frame = self.frame
        # print(type(frame))
        # print(frame.shape)
        corners, ids, rejectedImgPoints = aruco.detectMarkers(frame, self.arucoDict, parameters=self.parameters)
        rvec, tvec, _ = aruco.estimatePoseSingleMarkers(corners, self.len, self.camMat, self.camDist)
        nMarkers = 0
        if ids is not None:
            nMarkers = ids.shape[0]
            if targetID is None:
                dists = ((tvec*tvec)[:,:,0] + (tvec*tvec)[:,:,2] + (tvec*tvec)[:,:,1])/2.91
                for i in range(nMarkers):
                    dists[i] = math.sqrt(dists[i])
                euAngels = np.empty((nMarkers,3))
                for i in range(nMarkers):
                    euAngels[i] = self.rvecToEulerAngel(np.array(rvec[i]))
                dict["ids"] = ids.tolist()
                dict["dists"] = dists.tolist()
                dict["euAngles"] = euAngels.tolist()
            else:
                idx = 0
                for i in range(nMarkers):
                    if ids[i] == targetID: idx = i
                dist = math.sqrt(math.pow(tvec[0,0,0],2)+math.pow(tvec[0,0,1],2)+math.pow(tvec[0,0,2]))/2.91
                euAngel = rvecToEulerAngel(rvec[idx])
                dict["ids"].append([targetID])
                dict["dists"].append([dist.tolist()])
                dict["euAngels"].append(euAngels.tolist())

        return dict

    def capture(self):
        # ======= Used on Pi =========
        import picamera
        camera = picamera.PiCamera()
        width = 1920
        height = 1088
        camera.resolution = (width, height)
        camera.sharpness = 100
        camera.iso = 800
        camera.brightness = 60
        frame = np.empty((width*height*3), dtype=np.uint8)

        # ======= Used on PC =========
        # cap = cv2.VideoCapture(0)
        # ret, frame = cap.read()
        # width = frame.shape[1]
        # height = frame.shape[0]

        arucoDict = aruco.DICT_6X6_250
        # while True:
        for i in range(1):
            camera.capture(frame, use_video_port=True, format='bgr')
            # ret, self.frame = cap.read() # Used on PC
            self.frame = frame.reshape((height, width, 3))
            output = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            output = cv2.cvtColor(output, cv2.COLOR_GRAY2BGR)
            cv2.imwrite("cap_img.jpg",output)
            print("cap")
            time.sleep(1)

    def main(self):

        # SUB socket setting
        ctx = zmq.Context()
        cmdSocket = ctx.socket(zmq.DEALER)
        cmdSocket.connect(self.cmdEndpoint)
        dataSocket = ctx.socket(zmq.SUB)
        dataSocket.set_hwm(3)
        dataSocket.setsockopt(zmq.SUBSCRIBE, b'')
        dataSocket.connect(self.imgEndpoint)

        # PUB socket setting
        outSocket = ctx.socket(zmq.PUB)
        outSocket.bind(self.markerEndpoint)

        cmdSocket.send_string('start')
        count = 0
        try:
            while True:
                count+=1
                print(count)
                data = dataSocket.recv(copy=False)
                # print("Buffer len: ", len(data.bytes))
                data = np.frombuffer(data, dtype=np.uint8)[:self.h*self.w]
                # print("Data shape: ", data.shape)
                frame = data.reshape((self.h,self.w))
                # output = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                # cv2.imwrite("img_"+str(i)+".jpg", output)
                resDict = self.detect(frame)
                if resDict["ids"].shape[0] != 0
                    print(resDict)
                outSocket.send_json(resDict)
        finally:
            cmdSocket.send_string('stop')


    def saveImg(self,filename):
        # print(self.frame.shape)
        if self.frame is not None:
            output = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            cv2.imwrite("img.jpg", output)
        else:
            print("None")

    def run(self):
        mainProcess = multiprocessing.Process(target=self.main)
        mainProcess.start()


if __name__ == "__main__":
    detector = MarkerDetector("CameraPara.json")
    detector.run()
    exit()
