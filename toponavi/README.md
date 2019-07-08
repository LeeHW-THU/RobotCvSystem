# pi-controllerd

## 部署

安装依赖
```shell
sudo pip3 install -r requirments.txt
```

将`toponavi`目录拷贝到`/home/pi`目录下，将`toponavi/systemd`中的文件拷贝到`/etc/systemd/system/`下:

```shell
sudo cp -r ~/toponavi/systemd/* /etc/systemd/system/
sudo systemctl daemon-reload
```

使用以下命令启动程序。

```shell
sudo systemctl start toponavi
```

并可使用`systemctl status "toponavi*"`查看状态

使用`journalctl -u 'toponavi*'`查看日志
