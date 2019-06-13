# Week 2 Report

## June 12th

### TODO List

* [x] 1. Install OpenCV for Python3；
* [x] 2. 在PC上是实现ARUCO绘制与检测；

---

## June 13th

### TODO list  

* [x] 1.  测试比较如下方法获取单张图片的效率；

   参数设定：分辨率640*480，通道数3
   |   方法   |  AVG TIME / 10 frames  |  fps |
   |----------|------------|------------------|
   |OpenCV直接调用摄像头|   ERROR        |ERROR
   |picamera.capture_continuous(use_video_port=True)|1.080s |9.25
   |picamera.capture(use_video_port=True)|0.426s|23.5
* [x] 2.  完成相机标定；
* [x] 3.  检测视野中的ARUCO;
* [ ] 4.  测算相对目标ARUCO的角度与距离；
* [ ] 5.  定位已知的ARUCO标记的的位置；
* [ ] 6.  绘制拓扑地图；

### Notes

1. PiCamera的基本参数设置

    ``` python
    camera.resolution = (720,480) # 设置分辨率
    ```

### Daily Log

1. 获取图像方法测试  
   1. 使用OpenCV直接读取摄像头数据
      1. 已做尝试:

            ``` python
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)

            for i in range(10):
                ret, frame = cap.read()
                filename = str(i)+'.jpeg'
                cv2.imwrite(filename, frame)
            ```

          1. 在`/etc/modules-load.d/modules.conf`文件中添加行`bcm2835-v4l2`;
          2. 在`/etc/modules-load.d/`目录下添加文件`rpi_camera.conf`，并在其中添加行`bcm2835-v4l2`；
          3. 重启；
      2. 失败，原因不明，错误`VIDIOC_QBUF: Invalid argument`，使用`cv2.imwrite()`得到的图像文件均为`0 Bytes`；
   2. 使用方法3获取的图像出现偏色现象，原因不明；
      1. 现已解决：只是第一张和个别张存在过曝、亮度不足、偏色的状况；
   3. 相机标定结果：
        ``` python
        # 内参矩阵
        mtx = np.array([
            [790.116295132984, 0, 372.3818809136757],
            [0, 789.3286269926093, 316.5558903679369],
            [0, 0, 1],
            ])
        # 畸变系数
        dist = np.array(
            [0.2172601829633974,
            -1.184338097941321,
            -0.003550107827648891,
            -0.001021168378948774,
            1.558024382554203])
        ```


