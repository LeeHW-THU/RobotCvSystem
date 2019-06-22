import numpy as np
import time
import cv2  
import cv2.aruco as aruco
import picamera  
import sys
sys.path.append("..")
from keyboard_read import *

#with np.load('webcam_calibration_output.npz') as X:  
#    mtx, dist, _, _ = [X[i] for i in ('mtx','dist','rvecs','tvecs')]

#mtx = 
#2946.48    0    1980.53
#0    2945.41    1129.25
#0    0    1

mtx = np.array([
        [790.116295132984, 0, 372.3818809136757],
        [0, 789.3286269926093, 316.5558903679369],
        [0, 0, 1],
        ])
#我的手机拍棋盘的时候图片大小是 4000 x 2250
#ip摄像头拍视频的时候设置的是 1920 x 1080，长宽比是一样的，
#ip摄像头设置分辨率的时候注意一下

dist = np.array( [0.2172601829633974, -1.184338097941321, -0.003550107827648891, -0.001021168378948774, 1.558024382554203] )
# PiRobot


video = "http://admin:admin@192.168.1.2:8081/"   # 手机ip摄像头
# 根据ip摄像头在你手机上生成的ip地址更改，右上角可修改图像分辨率

# PC MyDearest-RTX
# cap = cv2.VideoCapture(0)
# PiRobot
camera = picamera.PiCamera()
camera.resolution = (720, 480)
camera.framerate = 24
frame = np.empty((720*480*3), dtype=np.uint8)



font = cv2.FONT_HERSHEY_SIMPLEX #font for displaying text (below)  

#num = 0
while True:  
    # get frame
    # ret, frame = cap.read() 
    camera.capture(frame, use_video_port=True, format='bgr')
    frame = frame.reshape((480,720,3))
    # operations on the frame come here  
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  
    aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)  
    parameters =  aruco.DetectorParameters_create()  
  
    '''
    detectMarkers(...) 
        detectMarkers(image, dictionary[, corners[, ids[, parameters[, rejectedI 
        mgPoints]]]]) -> corners, ids, rejectedImgPoints 
    '''  
      
    #lists of ids and the corners beloning to each id  
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, 
                                                          aruco_dict, 
                                                          parameters=parameters)  
  
#    if ids != None: 
    if ids is not None:
          
        rvec, tvec, _ = aruco.estimatePoseSingleMarkers(corners, 0.05, mtx, dist) 
        # Estimate pose of each marker and return the values rvet and tvec---different 
        # from camera coeficcients  
        (rvec-tvec).any() # get rid of that nasty numpy value array error  
        
#        aruco.drawAxis(frame, mtx, dist, rvec, tvec, 0.1) #Draw Axis  
#        aruco.drawDetectedMarkers(frame, corners) #Draw A square around the markers
        
        for i in range(rvec.shape[0]):
            aruco.drawAxis(frame, mtx, dist, rvec[i, :, :], tvec[i, :, :], 0.03)
            aruco.drawDetectedMarkers(frame, corners)
        ###### DRAW ID #####  
#        cv2.putText(frame, "Id: " + str(ids), (0,64), font, 1, (0,255,0),2,cv2.LINE_AA)  
  
  
    else:  
        ##### DRAW "NO IDS" #####  
        cv2.putText(frame, "No Ids", (0,64), font, 1, (0,255,0),2,cv2.LINE_AA)  
  
    # Display the resulting frame  
    #cv2.imshow("frame",frame)  
    # Write the resulting frame back to disk
    # cv2.imwrite("result.jpg",frame)
    # break
    print("Wait Key")
    key = readkey()
    
    if key == 'q':         # 按q退出
        print('esc break...')  
        camera.release()
        cv2.destroyAllWindows()
        break
    
    if key == ' ':   # 按空格键保存
#        num = num + 1
#        filename = "frames_%s.jpg" % num  # 保存一张图像
        print("Save file")
        filename = str(time.time())[:10] + ".jpg"  
        cv2.imwrite(filename, frame)