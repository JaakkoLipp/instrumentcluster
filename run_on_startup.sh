  GNU nano 7.2                                        run_on_startup.sh *                                               #!/bin/bash

# Run startAPI.sh
/home/pi/startAPI.sh

# Run main.py
cd /home/pi/instrumentcluster && screen -dmS main /usr/bin/python3 /home/pi/instrumentcluster/main.py