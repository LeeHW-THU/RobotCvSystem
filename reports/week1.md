x# 第一周周报

## 工作内容

* 设置WLAN为自动连接我们的电脑/手机/路由器的热点：连接信息写入[配置文件](../wpa_supplicant.conf)，位于树莓派上`/etc/wpa_supplicant/wpa_supplicant.conf`
* 重新焊接9号左后轮电机的一根连接线
* 检查并了解如何使用机器人基本功能
  * [x] 电机运动：分左右两组控制，每组分别由两个GPIO控制，分别控制前进和后退，可用PWM控制速度
  * [x] 摄像头
  * [ ] 红外传感器
  * [x] 超声波传感器
* 已实现基本遥控功能（path: ../JingoLan/motion_test.py）
