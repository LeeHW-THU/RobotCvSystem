

# 连接机器人

打开机器人电源

电脑连接机器人wifi热点，热点名称：Pi_RobotXX，其中XX为机器人编号

ssh登陆树莓派，账号：pi，密码：raspberry

```
ssh pi@10.3.141.1
```



# 停止机器人原有服务

```
sudo systemctl disable viple
```



# 摄像头

运行系统使用摄像头

```
sudo raspi-config
```

Interfacing Options  -   Enable camera  -  yes 

重启系统



拍摄图片

```
raspistill -o a.jpg
```



安装python-picamera

```
sudo apt-get install python-picamera
```

捕捉图片

```
python ./capture.py
```



# 运动

```
python ./motion.py
```

注意：放置机器人在地上运行！！！



# 超声波

```
python ./sonar.py
```

返回距离，单位厘米



# 安装opencv

安装依赖包
```
sudo apt-get install libhdf5-dev libhdf5-serial-dev
sudo apt-get install libqtwebkit4 libqt4-test
sudo apt-get install libatlas-base-dev libjasper-dev
```
安装opencv-python
```
sudo pip3 install opencv-contrib-python
```
测试
```
$ python3
Python 3.5.3 (default, Sep 27 2018, 17:25:39) 
[GCC 6.3.0 20170516] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import cv2
>>> cv2.__version__
'3.4.4'
```



# raspAP

USER: admin

Passwd: secret