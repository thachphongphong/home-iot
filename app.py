"""
A small Test application to show how to use Flask-MQTT.
"""
import logging
import eventlet
import json
import schedule
import time
import os.path
import configparser
import sqlite3 as sql
from flask import Flask, render_template, g, request
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap
from threading import Thread

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "iot.db")

# Blueprints
from api.api import api

eventlet.monkey_patch()

app = Flask(__name__)

iot_error_logger = logging.getLogger('iot.error')
app.logger.handlers.extend(iot_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)
app.logger.debug('START IOT API')

app.register_blueprint(api)

# app.config['SECRET'] = 'my secret key'
config = configparser.ConfigParser()
config.read('config.ini')

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = config['DEFAULT']['MQTT_BROKER_URL']
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_CLIENT_ID'] = 'iot-home'
app.config['MQTT_USERNAME'] = config['DEFAULT']['MQTT_USERNAME']
app.config['MQTT_PASSWORD'] = config['DEFAULT']['MQTT_PASSWORD']
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

devices = ["sonoff1","sonoff2","sonoff-valve"]
status = ["off","off","off"]

mqtt = Mqtt(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)

def checkDevice(d):
    if d in devices:
        return True
    else:
        return False


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sql.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/iot')
def index():
    cur = get_db().cursor()
    cur = cur.execute("select * from timer")
    rows = cur.fetchall()
    return render_template('index.html', timers=rows)


# @socketio.on('publish')
# def handle_publish(json_str):
#     data = json.loads(json_str)
#     if checkTopic(data['topic']):
#         mqtt.publish(data['topic'], data['message'], data['qos'])




# @socketio.on('subscribe')
# def handle_subscribe(json_str):
#     print("xxxxxxxxxx", json_str)
#     data = json.loads(json_str)
#     if checkTopic(data['topic']):
#         mqtt.subscribe(data['topic'], data['qos'])

@app.route('/api/v1.0/<devId>', methods=['GET'])
def get_light_status(devId):
    for idx, id in enumerate(devices):
        app.logger.debug("ID : %s"  % id)
        if(id == devId):
            app.logger.debug("GET /api/v1.0/%s: %s:" % (devId,status[idx]))
            return status[idx]
    return ""

@app.route('/api/v1.0/<devId>', methods=['POST'])
def post_light_status(devId):
    for idx, id in enumerate(devices):
        if(id == devId):
            global status
            if(status[idx] == 'on'):
                status[idx] = 'off'
            else:
                status[idx] = 'on'
            topic = "cmnd/"+id+"/power"
            app.logger.debug("POST /api/v1.0/%s: %s" % (topic, status[idx]))
            mqtt.publish(topic, status[idx], 2)
            socketio.emit('mqtt_message')
            return status[idx]
    return ''

@app.route('/api/v1.0/status', methods=['GET'])
def get_all_status():
    global status
    return json.dumps(status)

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode(),
        qos=message.qos,
    )
#    app.logger.debug("on_message %s: %s: %s " % (client, userdata, message.payload.decode()))
    global status
    for idx, id in enumerate(devices):
        topic = "stat/"+id+"/POWER"
        if(topic == message.topic):
            app.logger.debug("on_message %s: %s: %s " % (idx, topic, message.payload.decode()))
            status[idx] =  message.payload.decode().lower()
            socketio.emit('mqtt_message')

# @mqtt.on_log()
# def handle_logging(client, userdata, level, buf):
#     # print(level, buf)
#     pass

# @mqtt.on_connect()
# def handle_connect(client, userdata, flags, rc):
#     #for id in devices:
#        # app.logger.debug("Subscribe device topic %s" % id)
#        # mqtt.subscribe("cmnd/"+id+"/power", 0)
#        # mqtt.subscribe("stat/"+id+"/POWER", 0)

@app.route('/home')
def start():
    return 'IOT HOME PROJECT!'

def timer_job():
    app.logger.debug("I'm working...")

@app.route('/api/v1.0/timer/<devId>/<int:timer>', methods=['POST'])
def add_to_schedule(devId, timer=1):
    if checkDevice(devId):
        app.logger.debug(json.dumps(request.json))
        # job = schedule.every()
        # if count == 1:
        #     if period == 'day':
        #         job = job.day
        #     elif period == 'hour':
        #         job = job.hour
        #     elif period == 'minute':
        #         job = job.minute
        #     elif period == 'second':
        #         job = job.second
        #     else:
        #         return "Invalid period " + period
        # else:
        #     if period == 'day':
        #         job = job.days
        #     elif period == 'hour':
        #         job = job.hours
        #     elif period == 'minute':
        #         job = job.minutes
        #     elif period == 'second':
        #         job = job.seconds
        #     else:
        #         return "Invalid period " + period
        # job.do(timer_job)
        return "OK"
    else:
        return "Device not found"

def run_schedule():
    while 1:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    t = Thread(target=run_schedule)
    t.start()
    socketio.run(app, host='0.0.0.0', use_reloader=True, debug=True)