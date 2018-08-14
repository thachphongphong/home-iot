"""
A small Test application to show how to use Flask-MQTT.
"""

import eventlet
import json
from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap

# Blueprints
from api.api import api

eventlet.monkey_patch()

app = Flask(__name__)

app.register_blueprint(api)

#app.config['SECRET'] = 'my secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = '192.168.77.150'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_CLIENT_ID'] = 'flask_mqtt'
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

topics= ["sonoff1", "sonoff2"]

mqtt = Mqtt(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)


def checkTopic(t):
    if t in topics:
        return True
    else:
        return False

@app.route('/iot')
def index():
    return render_template('index.html')


@socketio.on('publish')
def handle_publish(json_str):
    data = json.loads(json_str)
    if checkTopic(data['topic']):
        mqtt.publish(data['topic'], data['message'], data['qos'])


@socketio.on('subscribe')
def handle_subscribe(json_str):
    data = json.loads(json_str)
    if checkTopic(data['topic']):
        mqtt.subscribe(data['topic'], data['qos'])


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode(),
        qos=message.qos,
    )
    socketio.emit('mqtt_message', data=data)


@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    # print(level, buf)
    pass

@app.route('/home')
def start():
    return 'IOT HOME PROJECT!'

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, use_reloader=True, debug=True)