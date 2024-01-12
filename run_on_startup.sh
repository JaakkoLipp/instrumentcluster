#!/bin/bash

# Run startAPI.sh
/home/pi/startAPI.sh

sleep 2

# Run main.py
screen -dmS main /usr/bin/python3 /home/pi/instrumentcluster/main.py
