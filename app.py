"""
A small Test application to show how to use Flask-MQTT.
"""

import eventlet
import json,logging
from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap

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
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = 'localhost'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_CLIENT_ID'] = 'iot-home'
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

devices = ["sonoff1","sonoff2","sonoff-valve"]
status = ["off","off","off"]

mqtt = Mqtt(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)

def checkTopic(t):
    return True
    if t in topics:
        return True
    else:
        return False

@app.route('/iot')
def index():
    return render_template('index.html')


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
    global status
    for idx, id in enumerate(devices):
        topic = "stat/"+id+"/POWER"
        if(topic == message.topic):
            app.logger.debug("on_message %s: %s: %s " % (idx, topic, message.payload.decode()))
            status[idx] =  message.payload.decode().lower()

# @mqtt.on_log()
# def handle_logging(client, userdata, level, buf):
#     # print(level, buf)
#     pass

@app.route('/home')
def start():
    return 'IOT HOME PROJECT!'

if __name__ == '__main__':
    for id in devices:
        topic = "cmnd/"+id+"/power"
        mqtt.subscribe(topic, 0)
    socketio.run(app, host='0.0.0.0', use_reloader=True, debug=True)