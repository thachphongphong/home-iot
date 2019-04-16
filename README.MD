# Steps
## DB
- sqlite3 iot
- CREATE TABLE timer (devId varchar(20) NOT NULL, timer int NOT NULL, period varchar(5) NOT NULL, at varchar(20) NOT NULL, action int NOT NULL);
- CREATE TABLE user (id integer PRIMARY KEY NOT NULL, username varchar(20) NOT NULL, password varchar(20) NOT NULL);
- CREATE TABLE status (devId varchar(20) PRIMARY KEY NOT NULL, status int NOT NULL);
- INSERT INTO status (devId, status) VALUES ('sonoff1', 0);
- INSERT INTO status (devId, status) VALUES ('sonoff2', 0);
- INSERT INTO status (devId, status) VALUES ('sonoff-valve', 1);
- CREATE TABLE device (username varchar(20) NOT NULL, devId varchar(20) NOT NULL, name varchar(20) NOT NULL, status int NOT NULL, power int NOT NULL, vol int NOT NULL, cat varchar(20) NOT NULL);
- INSERT INTO device (username, devId, name, status, power, vol, cat) VALUES ('ldt', 'sonoff1', 'Front door', 1, 24, 220, 'light');

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
- docker volume create --name mqtt_data

- docker run --name mqtt --restart=always --net=host -tid -v /mqtt/config/mosquitto.conf:/mqtt/config/mosquitto.conf -v /mqtt/log:/mqtt/log -v mqtt_data:/mqtt/data/ toke/mosquitto

### api
-  docker run -dit --net=host -p 5000:5000 -v {{PATH}}/api:/home/iot  
   {{PATH}}/iot.db:/home/iot/iot.db iot-api
### scheduler
- docker run -dit --name=scheduler 
-v {{PATH}}/scheduler:/home/iot {{PATH}}/iot.db:/home/iot/iot.db iot-scheduler