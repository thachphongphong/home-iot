"""
A small Test application to show how to use Flask-MQTT.
"""
import logging
import eventlet
import json
import os.path
import configparser
import sqlite3 as sql

import pytz
from flask import Flask, render_template, g, request, abort, session, redirect, url_for
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "iot.db")

eventlet.monkey_patch()

app = Flask(__name__)
app.secret_key = os.urandom(12)

iot_error_logger = logging.getLogger('iot.error')
app.logger.handlers.extend(iot_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)
app.logger.debug('START IOT API')

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
schedule_topic = "topic/schedule"

mqtt = Mqtt(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)

## MQTT ##
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode(),
        qos=message.qos,
    )
    app.logger.debug("on_message %s: %s: %s " % (client, userdata, data['payload']))
    for id in devices:
        topic = "stat/"+id+"/POWER"
        if(topic == data['topic']):
            app.logger.debug("topic status change  %s: %s " % (topic, data['payload']))
            status = 1 if data['payload'].lower() == 'on' else 0;
            with app.app_context():
                try:
                    db = get_db()
                    cur = db.cursor()
                    cur.execute("UPDATE status SET status=? WHERE devId=?", (status, id))
                    db.commit()
                    app.logger.debug("Success update status db  %s: %s " % (id, status))
                except sql.Error as e:
                    app.logger.debug("Database error: %s" % e)
            socketio.emit('mqtt_message')

# @mqtt.on_log()
# def handle_logging(client, userdata, level, buf):
#     # print(level, buf)
#     pass

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

## FUNCTION ##

def checkToken(request):
    token = request.headers.get('Authorization')
    if(token == 'Bearer hWd3uNMVpjaRAbPs9Nt3'):
        return True
    return False

def checkDevice(d):
    if d in devices:
        return True
    else:
        return False

def get_status(s):
    if s == 1:
        return 'ON'
    elif s == 0:
        return 'OFF'
    else:
        return ''

def toUtc(at):
    naive = datetime.now()
    la_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    at = datetime.strptime(at, "%H:%M")

    with_tz = la_tz.localize(naive.replace(hour=at.hour, minute=at.minute))
    converted_to_utc = with_tz.astimezone(pytz.utc)
    return converted_to_utc.strftime("%H:%M")

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sql.connect(DATABASE)
    return db

def checkUser(username, password):
    app.logger.debug("Login with %s - %s" % (username,password))
    cur = get_db().cursor()
    cur = cur.execute("SELECT * FROM user WHERE username=? AND password=?", (username,password))
    data = cur.fetchone()
    if data is None:
        return False
    return True

## FRONT END ##
@app.route('/')
def start():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        return render_template('home.html')

@app.route('/lights')
def lights():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        return render_template('lights.html')

@app.route('/iot')
def index():
    return render_template('index.html')

@app.route('/login',methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = str(request.form.get('username'))
        password = str(request.form.get('password'))
        if checkUser(username, password):
            app.logger.debug("Login with %s", username)
            session['logged_in'] = True
            return redirect(url_for('start'))
        else:
            app.logger.debug("Login is invalid")
            error = 'Wrong username or password!'
            return render_template('login.html', error = error)
    else:
        return render_template('login.html')

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))

@app.template_filter()
def toLocal(at):
    naive = datetime.now()
    utc_tz = pytz.timezone("UTC")
    at = datetime.strptime(at, "%H:%M")

    with_tz = utc_tz.localize(naive.replace(hour=at.hour, minute=at.minute))
    converted_to_lc = with_tz.astimezone(pytz.timezone("Asia/Ho_Chi_Minh"))
    return converted_to_lc.strftime("%H:%M")
app.jinja_env.filters['tolocal'] = toLocal

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

## API ##

@app.route('/api/v1.0/<devId>', methods=['GET'])
def get_light_status(devId):
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    try:
        db = get_db()
        db.row_factory = sql.Row
        cur = db.cursor()
        rs = cur.execute("SELECT * FROM status WHERE devId=?", (devId,))
        row = rs.fetchone()
        return json.dumps({'devId': row[0], 'status': row[1]})
    except sql.Error as e:
        app.logger.debug("Database error: %s" % e)
    return ""

@app.route('/api/v1.0/<devId>', methods=['POST'])
def post_light_status(devId):
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    data = request.json
    if (data is None or data['status'] is None):
        app.logger.debug("Status is missing")
        abort(500)
    try:
        db = get_db()
        db.row_factory = sql.Row
        cur = db.cursor()
        rs = cur.execute("SELECT * FROM status WHERE devId=?", (devId,))
        row = rs.fetchone()
        if row is None:
            app.logger.debug("Device not found %s", (devId))
            abort(404)
        if( data['status'] != row[1]):
            topic = "cmnd/"+devId+"/power"
            status = 'on' if data['status'] == 1 else 'off';
            app.logger.debug("POST /api/v1.0/%s: %s" % (topic, status))
            mqtt.publish(topic, status, 2)
            # socketio.emit('mqtt_message')
        return json.dumps({'devId': row[0], 'status': data['status']})
    except sql.Error as e:
        app.logger.debug("Database error: %s" % e)
    return ''

@app.route('/api/v1.0/status', methods=['GET'])
def get_all_status():
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    try:
        db = get_db()
        db.row_factory = sql.Row
        cur = db.cursor()
        rs = cur.execute("SELECT * FROM status")
        items = []
        for row in rs:
            items.append({'devId': row[0], 'status': row[1]})
        return json.dumps(items)
    except sql.Error as e:
        app.logger.debug("Database error: %s" % e)
    return ""

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    for id in devices:
       app.logger.debug("Subscribe device topic %s" % id)
       mqtt.subscribe("stat/"+id+"/POWER", 0)

@app.route('/api/v1.0/timer', methods=['GET'])
def get_timers():
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    try:
        db = get_db()
        db.row_factory = sql.Row
        cur = db.cursor()
        rs = cur.execute("SELECT * FROM timer ORDER BY devId, timer")
        items = []
        for row in rs:
            items.append({'devId': row[0], 'timer': row[1], 'period': row[2], 'at': toLocal(row[3]),'action': row[4]})
        return json.dumps(items)
    except sql.Error as e:
        app.logger.debug("Database error: %s" % e)
    return ""


@app.route('/api/v1.0/timer/<devId>', methods=['GET'])
def get_timer(devId):
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    if checkDevice(devId):
        try:
            db = get_db()
            db.row_factory = sql.Row
            cur = db.cursor()
            rs = cur.execute("SELECT * FROM timer WHERE devId=?", (devId,))
            items = []
            for row in rs:
                items.append({'devId': row[0], 'timer': row[1], 'period': row[2], 'at': toLocal(row[3]),'action': row[4]})
            return json.dumps(items)
        except sql.Error as e:
            app.logger.debug("Database error: %s" % e)
        return ""
    else:
        abort(404)
        return "Device not found"

@app.route('/api/v1.0/timer/<devId>/<int:timer>', methods=['POST'])
def add_to_schedule(devId, timer=1):
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    if checkDevice(devId):
        try:
            data = request.json
            data['at'] = toUtc(data['at'])
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT * FROM timer WHERE devId=? AND timer=?", (devId,timer))
            row = cur.fetchall()
            if len(row)==0:
                app.logger.debug("ADD NEW %s", data)
                cur.execute("INSERT INTO timer VALUES(?,?,?,?,?)", (devId, timer, data['period'], data['at'], data['action']))
                data["type"] = "ADD"
                data["devId"] = devId
                data["timer"] = timer
                mqtt.publish(schedule_topic, json.dumps(data), 2)
            else:
                app.logger.debug("REPLACE DATA %s", data)
                cur.execute("UPDATE timer SET period=?, at=?, action=? WHERE devId=? AND timer=?", (data['period'], data['at'], data['action'], devId, timer))
                data["type"] = "REPLACE"
                data["devId"] = devId
                data["timer"] = timer
                mqtt.publish(schedule_topic, json.dumps(data), 2)
            db.commit()
            app.logger.debug("Record successfully added %s", timer)
            return json.dumps({'devId': devId, 'timer': timer, 'period': data['period'], 'at': toLocal(data['at']), 'action': data['action']})
        except sql.Error as e:
            db.rollback()
            app.logger.debug("Database error: %s" % e)
        except Exception as e:
            db.rollback()
            app.logger.debug("Exception in _query: %s" % e)
        # finally:
        #     db.close()
        return ""
    else:
        abort(404)
        return "Device not found"

@app.route('/api/v1.0/timer/<devId>/<int:timer>', methods=['DELETE'])
def delete_schedule(devId, timer=1):
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    if checkDevice(devId):
        try:
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT * FROM timer WHERE devId=? AND timer=?", (devId,timer))
            row = cur.fetchone()
            if not row is None:
                app.logger.debug("DELETE TIMER %s %s" % (devId, timer))
                cur.execute("DELETE FROM timer WHERE devId=? AND timer=?", (devId,timer))
                db.commit()
                app.logger.debug("Record successfully deleted %s", timer)
                data = {"devId": row[0], "timer": row[1], "period": row[2], "at": toUtc(row[3]), "action": row[4]}
                data["type"] = "REMOVE"
                mqtt.publish(schedule_topic, json.dumps(data), 2)
        except sql.Error as e:
            db.rollback()
            app.logger.debug("Database error: %s" % e)
        except Exception as e:
            db.rollback()
            app.logger.debug("Exception in _query: %s" % e)
        # finally:
        #     db.close()
        return ""
    else:
        abort(404)
        return "Device not found"
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', use_reloader=True, debug=True)