# blueos_webinterface
Creating a local web interface through blueos.
In this repository, it documents how a gps tracker is connect to raspberry pi and hosts a local webinterface inside blueos.

First try to open the terminal, make sure it is pi and not blueos. If is in blueos, type red-pill.
The 'my-gps-tracker' is already in the raspberry pi. Check by typing ls.

Then build the docker image and execcute these commands:

'''
sudo docker build -t local/my-gps-tracker .

sudo docker run --network host local/my-gps-tracker
'''

Once you run these codes are executed, Check in the local webserver:
'''http://192.168.2.2:8080'''
