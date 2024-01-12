#!/bin/bash

# Run startAPI.sh
/home/pi/instrumentcluster/startAPI.sh

sleep 2

# Run main.py
/usr/bin/python3 /home/pi/instrumentcluster/main.py
