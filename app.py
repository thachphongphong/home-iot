"""
A small Test application to show how to use Flask-MQTT.
"""
from importlib import import_module
import os
import eventlet
from flask import Flask, render_template, Response
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap

# import camera driver
if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    from camera_opencv import Camera

# Blueprints
from api.api import api

eventlet.monkey_patch()

app = Flask(__name__)

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

devices = ["sonoff2","sonoff1"]
status = ["off","off"]

mqtt = Mqtt(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)

tmp_dir = '/tmp/'
tmp_filename = 'snapshot.jpg'

def checkTopic(t):
    return True
    if t in topics:
        return True
    else:
        return False

@app.route('/iot')
def index():
    return render_template('index.html')

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

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

@app.route('/api/v1.0/light/<devId>', methods=['GET'])
def get_light_status(devId):
    for idx, id in enumerate(devices):
        if(id == devId):
            print("GET /api/v1.0/light/ %s:" % status[idx])
            return status[idx]
    return ""

@app.route('/api/v1.0/light/<devId>', methods=['POST'])
def post_light_status(devId):
    for idx, id in enumerate(devices):
        if(id == devId):
            global status
            if(status[idx] == 'on'):
                status[idx] = 'off'
            else:
                status[idx] = 'on'
            topic = "cmnd/"+id+"/power"
            print("POST /api/v1.0/light/ %s: %s" % (topic, status[idx]))
            mqtt.publish(topic, status[idx], 2)
            socketio.emit('mqtt_message')
            return status[idx]
    return ''


# @mqtt.on_message()
# def handle_mqtt_message(client, userdata, message):
#     data = dict(
#         topic=message.topic,
#         payload=message.payload.decode(),
#         qos=message.qos,
#     )
#     print("on_message %s: %s: %s " % (client, userdata, message.payload.decode()))
#     global status
#     for idx, id in enumerate(devices):
#         topic = "cmnd/"+id+"/power"
#         if(topic == message.topic):
#             print("on_message %s: %s: %s " % (idx, topic, message.payload.decode()))
#             status[idx] =  message.payload.decode()
#             socketio.emit('mqtt_message', data=data)

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