# pi-controllerd

pi-controller Android APP的服务端守护进程，具有远程遥控，传输图像的能力

## 部署

安装依赖
```shell
sudo apt install
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    python3-gst-1.0
```

将pi-controllerd目录拷贝到`/home/pi`目录下，将pi-controllerd.service文件拷贝到`/etc/systemd/system/pi-controllerd.service`，使用以下命令启动程序。

```shell
sudo systemctl enable pi-controllerd.service
sudo systemctl start pi-controllerd.service
```

并可使用`systemctl status pi-controllerd.service`查看状态
