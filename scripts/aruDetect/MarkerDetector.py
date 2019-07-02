import numpy as np
import math
import time
import cv2  
import cv2.aruco as aruco
import json
#import picamera  

# class MarkerDetector:
#     def __init__(self, camMat, camDist, dictID, len):
#         self.camMat = camMat
#         self.camDist = camDist
#         self.len = len
#         self.aruco_dict = aruco.Dictionary_get(dictID)  
#         self.parameters =  aruco.DetectorParameters_create()

#     #Arg: 
#     #   frame: a numpy.array with shape(height, width, channels)
#     def detectMarker(self, frame, targetID):
#         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  
       
#         corners, ids, rejectedImgPoints = aruco.detectMarkers(frame, 
#                                                             self.aruco_dict, 
#                                                             parameters=self.parameters)
#         if ids is not None:
#             idx = -1
#             for j in range(ids.shape[0]):
#                 if ids[j,0] == targetID: 
#                     idx = j
#             if idx == -1: return None
#             return corners[idx]
        
#         return None

class MarkerDetector:
    def __init__(self, camConfFile, arucoDict, len):
        with open(camConfFile, "r") as f:
            camPara = json.load(f)
            self.camMat = np.array(camPara["Mat"])
            self.camDist = np.array(camPara["Dist"])
            self.len = len
            self.arucoDict = aruco.Dictionary_get(arucoDict)  
            self.parameters =  aruco.DetectorParameters_create()
    
    def rvecToEulerAngel(self, rvec):
        rMat = cv2.Rodrigues(rvec[0])[0]
        # print(rMat)

        # thetaX = math.atan2(rMat[1, 0], rMat[0, 0])*180.0/math.pi
        # thetaY = math.atan2(-1.0*rMat[2, 0], math.sqrt(rMat[2, 1]**2 + rMat[2, 2]**2))*180.0/math.pi
        # thetaZ = math.atan2(rMat[2, 1], rMat[2, 2])*180.0/math.pi
        # euAngel = np.array(euAngel)
        # euAngel = [thetaX, thetaY, thetaZ]

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
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejectedImgPoints = aruco.detectMarkers(frame, self.arucoDict, parameters=self.parameters)
        # print(self.camMat)
        rvec, tvec, _ = aruco.estimatePoseSingleMarkers(corners, self.len, self.camMat, self.camDist)
        if ids is not None:
            nMarkers = ids.shape[0]
            if targetID is None:
                dists = ((tvec*tvec)[:,:,0] + (tvec*tvec)[:,:,2])/1.48
                for i in range(nMarkers):
                    dists[i] = math.sqrt(dists[i])
                euAngels = np.empty((nMarkers,3))
                for i in range(nMarkers):
                    euAngels[i] = self.rvecToEulerAngel(np.array(rvec[i]))
                return ids, dists, euAngels
            else:
                idx = 0
                for i in range(nMarkers):
                    if ids[i] == targetID: idx = i
                dist = math.sqrt(math.pow(tvec[0,0,0],2)+math.pow(tvec[0,0,1],2))/1.48
                euAngel = rvecToEulerAngel(rvec[idx])
                return dist, euAngel
        return None, None, None

if __name__ == "__main__":
    import picamera
    camera = picamera.PiCamera()
    width = 1648
    height = 1232
    camera.resolution = (width, height)
    camera.sharpness = 100
    camera.iso = 800
    camera.brightness = 60
    frame = np.empty((width*height*3), dtype=np.uint8)
    
    # print(width,end=',')
    # print(height)
    
    # ======= Used on PC =========
    # cap = cv2.VideoCapture(0)
    # ret, frame = cap.read()
    # width = frame.shape[1]
    # height = frame.shape[0]

    arucoDict = aruco.DICT_6X6_250
    detector = MarkerDetector("CameraPara.json",arucoDict, 10)
    while True:
        camera.capture(frame, use_video_port=True, format='bgr')
        # ret, frame = cap.read() # Used on PC

        frame = frame.reshape((height, width, 3))
        ids, dists, euAngels = detector.detect(frame)
        if ids is not None:
            print(ids)
            print(euAngels)
        else: print("Could not detect")
        key=cv2.waitKey(1)
    pass