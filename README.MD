# Steps
## DB
- sqlite3 iot
- CREATE TABLE timer (devId integer, timer integer, period text, at text);

## Install
- sudo apt-get install python-dev
- sudo pip install virtualenv
- sudo /usr/bin/easy_install virtualenv
- virtualenv home-iot
- source home-iot/bin/activate
- pip install -r requirements.txt

## Web server
- sudo pip install gunicorn
- sudo touch /var/log/iot.log
- sudo chmod uag+rw /var/log/iot.log
- sudo mv iot.service /etc/systemd/system/iot.service
- sudo apt-get install nginx
- sudo mv iot.conf /etc/nginx/conf.d/iot.conf

## debug
- gunicorn --worker-class eventlet --log-level debug --bind 0.0.0.0:500 app

## docker

### api
-  docker run -it --rm -p 5000:5000 -v {{PATH}}/home-iot/api:/home/iot  
    -v {{PATH}}/home-iot/iot.db:/home/iot/iot.db iot-api:latest
### api
- docker run --net=host --name=scheduler -v /home/ldt/iot/home-iot/scheduler:/home/iot  -v /home/ldt/iot/home-iot/iot.db:/home/iot/iot.db -d iot-scheduler