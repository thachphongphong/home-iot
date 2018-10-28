# Steps

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