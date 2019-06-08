#!/bin/bash

HOST="192.168.137.69"

rsync -rt --delete --exclude "**/__pycache__" pi-controllerd pi@$HOST:/home/pi/
