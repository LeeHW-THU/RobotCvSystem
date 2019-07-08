#!/bin/bash

HOST="192.168.137.93"

rsync -rt --delete --exclude "**/__pycache__" pi-controllerd pi@$HOST:/home/pi/
ssh pi@$HOST "sudo systemctl restart pi-controllerd.service"
