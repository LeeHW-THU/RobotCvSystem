import picamera
import time
from time import sleep

camera = picamera.PiCamera()

start_time=time.time()
for i in range(30):
	camera.capture('image01.jpg',use_video_port=True)
print time.time() - start_time