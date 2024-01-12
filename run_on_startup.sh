#!/bin/bash

# Run startAPI.sh
/home/pi/startAPI.sh

# Run main.py
screen -dmS main cd /home/pi/instrumentcluster && /usr/bin/python3 /home/pi/instrumentcluster/main.py
