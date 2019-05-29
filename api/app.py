"""
A small Test application to show how to use Flask-MQTT.
"""
import logging
import eventlet
import json
import os.path
import configparser
import sqlite3 as sql
import re

import pytz
from flask import Flask, render_template, g, request, abort, session, redirect, url_for
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap
from datetime import datetime, timedelta

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

env_profile = config['DEFAULT']['ENV_PROFILE']
schedule_topic = "topic/schedule"

mqtt = Mqtt(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)

## MQTT ##
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    app.logger.debug("MQTT is connected")
    with app.app_context():
        subscribe()

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode(),
        qos=message.qos,
    )
    app.logger.debug("on_message %s: %s: %s " % (data['topic'], data['payload'], data['qos']))
    with app.app_context():
        try:
            app.logger.debug("Message receive: %s" % data['topic'])
            # Can check by query to db
            if(re.match("stat/.*/POWER", data['topic'])):
                devId = data['topic'].replace("stat/","").replace("/POWER","")
                status = 1 if data['payload'].lower() == 'on' else 0;
                db = get_db()
                cur = db.cursor()
                cur.execute("UPDATE status SET status=? WHERE devId=?", (status, devId))
                cur.execute("INSERT INTO log VALUES(?,?,?)", (devId, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                db.commit()
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
def subscribe():
    for row in getUserDevice(None):
       mqtt.subscribe("stat/"+row[1]+"/POWER", 0)

def un_subscribe(devId):
    for dev in get_devices():
       mqtt.unsubscribe("stat/"+devId+"/POWER")

def get_devices():
    devices = []
    if session.get('devices'):
        for dev in session.get('devices',[]):
            devices.append(
                dict(username = dev[0],
                devId = dev[1],
                name = dev[2],
                status = dev[3], 
                power = dev[4],
                vol = dev[5],
                cat = dev[6],
                icon = dev[7]
                )
            )
    return devices

def get_devices_by_cat(cat):
    cats = []
    for dev in get_devices():
        if(dev['cat'] == cat):
            cats.append(dev)
    return cats

def checkToken(request):
    token = request.headers.get('Authorization')
    if(token == 'Bearer hWd3uNMVpjaRAbPs9Nt3'):
        return True
    return False

def checkDevice(id):
    for dev in get_devices():
        if id == dev['devId']:
            return True
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
    app.logger.debug("Login with %s - %s" % (username, 'xxxxxxxxx'))
    try:
        cur = get_db().cursor()
        cur = cur.execute("SELECT * FROM user WHERE username=? AND password=?", (username,password))
        data = cur.fetchone()
        if data is not None:
            return True
    except sql.Error as e:
        app.logger.debug("Database error: %s" % e)
    return False

def getUserDevice(username):
    app.logger.debug("Load devices for user %s" % (username,))
    try:
        cur = get_db().cursor()
        if not username:
            cur = cur.execute("SELECT * FROM device")
        else:
            cur = cur.execute("SELECT * FROM device WHERE username=?", (username,))
        devices = cur.fetchall()
        return devices
    except sql.Error as e:
        app.logger.debug("Database error: %s" % e)
    return []

def refresh_device_session():
    if 'username' in session:
        session['devices'] = getUserDevice(session.get('username'))

def getUsername(request):
    username = session.get('username')
    if username is None:
        username = request.headers.get('user-id')
    return username

def checkUserId(request):
    username = request.headers.get('user-id')
    if username is not None:
        try:
            cur = get_db().cursor()
            cur = cur.execute("SELECT * FROM user WHERE username=?", (username,))
            data = cur.fetchone()
            if data is not None:
                return True
        except sql.Error as e:
            app.logger.debug("Database error: %s" % e)
        return False

## FRONT END ##
@app.route('/')
def start():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        lights = []
        others = []
        for dev in get_devices():
            if(dev['cat'] == 'light'):
                lights.append(dev)
            else:
                others.append(dev)
        return render_template('home.html', lights = lights, others = others)

@app.route('/lights')
def lights():
    if not session.get('logged_in'):
        session['url'] = url_for('lights')
        return redirect(url_for('login'))
    else:
        return render_template('lights.html', lights = get_devices_by_cat('light'))

@app.route('/hydroponic')
def hydroponic():
    if not session.get('logged_in'):
        session['url'] = url_for('hydroponic')
        return redirect(url_for('login'))
    else:
        return render_template('hydroponic.html', hydro = get_devices_by_cat('hydroponic'))

@app.route('/settings')
def settings():
    if not session.get('logged_in'):
        session['url'] = url_for('settings')
        return redirect(url_for('login'))
    else:
        return render_template('settings.html')

@app.route('/camera')
def camera():
    if not session.get('logged_in'):
        session['url'] = url_for('camera')
        return redirect(url_for('login'))
    else:
        return render_template('camera.html', name = config['DEFAULT']['CAMERA_USERNAME'], pss = config['DEFAULT']['CAMERA_PASSWORD'])

@app.route('/iot')
def index():
    return 'UP'

@app.route('/login',methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = str(request.form.get('username'))
        password = str(request.form.get('password'))
        if checkUser(username, password):
            app.logger.debug("Login with %s", username)
            session['logged_in'] = True
            session['username'] = username
            session['devices'] = getUserDevice(username)
            if 'url' in session:
                return redirect(session['url'])
            return redirect(url_for('start'))
        else:
            app.logger.debug("Login is invalid")
            error = 'Wrong username or password!'
            return render_template('login.html', error = error)
    else:
        return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
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
    if checkDevice(devId) or checkUserId(request):
        try:
            db = get_db()
            db.row_factory = sql.Row
            cur = db.cursor()
            rs = cur.execute("SELECT * FROM status WHERE devId=?", (devId,))
            row = rs.fetchone()
            if row is None:
                cur.execute("INSERT INTO status VALUES(?,?)",(devId,0))
                db.commit()
            elif(data['status'] != row[1]):
                topic = "cmnd/"+devId+"/power"
                status = 'on' if data['status'] == 1 else 'off';
                app.logger.debug("POST /api/v1.0/%s: %s" % (topic, status))
                mqtt.publish(topic, status, 2)
                if env_profile == 'LOCAL':
                    mqtt.publish("stat/"+devId+"/POWER", status, 2)
                    # socketio.emit('mqtt_message')
            return json.dumps({'devId': devId, 'status': data['status']})
        except sql.Error as e:
            app.logger.debug("Database error: %s" % e)
    else:
        app.logger.debug("Device not found %s", (devId))
        abort(404)
    return ''

@app.route('/api/v1.0/status', methods=['GET'])
def get_all_status():
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    try:
        username = getUsername(request)
        db = get_db()
        db.row_factory = sql.Row
        cur = db.cursor()
        rs = cur.execute("SELECT * FROM status where devId IN (SELECT devId FROM device WHERE username=?)", (username,))
        map = {}
        status = []
        for row in rs:
            map.setdefault(row[0],row[1])
            status.append({'devId': row[0], 'status': row[1]})
        items = []
        for d in get_devices():
            status = 0
            if(d['devId'] in map):
                status = map[d['devId']]
            items.append({'devId': d['devId'], 'status': status, 'cat': d['cat']})
        if 'username' in session:
                return json.dumps(items)
        else:
            return json.dumps(status)
    except sql.Error as e:
        app.logger.debug("Database error: %s" % e)
    return ""

@app.route('/api/v1.0/timer', methods=['GET'])
def get_timers():
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    try:
        username = getUsername(request)
        db = get_db()
        db.row_factory = sql.Row
        cur = db.cursor()
        rs = cur.execute("SELECT * FROM timer WHERE devId IN (SELECT devId FROM device WHERE username=?) ORDER BY devId, timer", (username,))
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

# LOG
@app.route('/api/v1.0/light-chart', methods=['GET'])
def chartLog():
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    try:
        dt = datetime.now()
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=6)
        db = get_db()
        db.row_factory = sql.Row
        cur = db.cursor()
        rs = cur.execute("SELECT * FROM log WHERE time >= ? AND time <= ? AND devId IN (SELECT devId FROM device WHERE username=? AND cat ='light') ORDER BY time", (start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S'), session.get('username')))
        map = {}
        tmp = {}
        series = []
        labels = []
        for row in rs:
            tmp.setdefault(row[2].split(" ")[0] + " - " + row[0], []).append({"s" : row[1], "t" : row[2]})

        for k, v in tmp.items():
            tdelta = 0
            ts = te = None
            for r in tmp[k]:
                if(r['s'] == 1):
                    ts = datetime.strptime(r['t'],'%Y-%m-%d %H:%M:%S')
                elif(r['s'] == 0):
                    te = datetime.strptime(r['t'],'%Y-%m-%d %H:%M:%S')
                    if ts is not None:
                        tdelta += (te - ts).total_seconds()
                        ts = te = None
            map.setdefault(k.split(" - ")[1],[]).append(divmod(tdelta, 60)[0])

        # Get device name
        for dev in get_devices_by_cat('light'):
            data = [0] * 7
            if(dev['devId'] in map):
                indx = 0
                for d in map[dev['devId']]:
                    data[indx] = d
                    indx += 1
            series.append({"name": dev['name'], "data": data})

        d = start
        while d <= end:
            labels.append(d.strftime('%a'))
            d += timedelta(days=1)

        return json.dumps({'labels': labels, 'series': series})
    except sql.Error as e:
        app.logger.debug("Database error: %s" % e)
    return ""

@app.route('/api/v1.0/hydro-chart', methods=['GET'])
def hydroChartLog():
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    try:
        start = datetime.now().astimezone(pytz.timezone("Asia/Ho_Chi_Minh")).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(1)
        db = get_db()
        db.row_factory = sql.Row
        cur = db.cursor()
        rs = cur.execute("SELECT * FROM log WHERE time >= ? AND time < ? AND devId IN (SELECT devId FROM device WHERE username=? AND cat ='hydroponic') ORDER BY time", (start.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S'), end.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S'), session.get('username')))
        series = []
        labels = []
        tdelta = 0
        map = {}
        ts = te = None
        for row in rs:
            if(row[1] == 1):
                 ts = datetime.strptime(row[2],'%Y-%m-%d %H:%M:%S').astimezone(pytz.timezone("Asia/Ho_Chi_Minh"))
            elif(row[1] == 0):
                te = datetime.strptime(row[2],'%Y-%m-%d %H:%M:%S').astimezone(pytz.timezone("Asia/Ho_Chi_Minh"))
                if ts is not None:
                    tdelta += (te - ts).total_seconds()
                    map.setdefault(row[0] + " - " + ts.strftime('%H:%M'),tdelta)
                    ts = te = None
                    tdelta = 0
        print(map)
        # Get device name
        for dev in get_devices_by_cat('hydroponic'):
            data = [0] * 48
            for k, v in map.items():
                id = k.split(' - ')[0]
                t = k.split(' - ')[1]
                if(dev['devId'] == id):
                    idx = int(t.split(':')[0]) * 2
                    if int(t.split(':')[1]) > 0:
                        idx += 1
                    data[idx] = map[k]
            series.append({"name": dev['name'], "data": data})

        d = start
        while d < end:
            labels.append(d.strftime('%H'))
            d += timedelta(minutes=30)

        return json.dumps({'labels': labels, 'series': series})
    except sql.Error as e:
        app.logger.debug("Database error: %s" % e)
    return ""

@app.route('/api/v1.0/device', methods=['GET'])
def get_user_devices():
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    try:
        username = getUsername(request)
        if username is not None:
            app.logger.debug("Get devices for user: %s" % username)
            db = get_db()
            db.row_factory = sql.Row
            cur = db.cursor()
            rs = cur.execute("SELECT * FROM device WHERE username=?", (username,))
            items = []
            for row in rs:
                items.append({'devId': row[1], 'name': row[2], 'status': row[3], 'power': row[4], 'vol': row[5], 'cat': row[6], 'icon': row[7]})
            if 'username' in session:
                return json.dumps({'data': items})
            else:
                return json.dumps(items)
    except sql.Error as e:
        app.logger.debug("Database error: %s" % e)
    return ""

@app.route('/api/v1.0/device', methods=['POST'])
def add_device():
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    try:
        username = session.get('username')
        data = request.json
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM device WHERE username=? AND devId=?", (username, data['devId']))
        row = cur.fetchall()
        if len(row)==0:
            app.logger.debug("Add new device %s", data)
            cur.execute("INSERT INTO device VALUES(?,?,?,?,?,?,?,?)", (username, data['devId'], data['name'], data['status'], data['power'], data['vol'], data['cat'], data['icon']))  
        else:
            app.logger.debug("Update device %s", data)
            cur.execute("UPDATE device SET devId=?, name=?, status=?, power=?, vol=?, cat=?, icon=? WHERE username=? AND devId=?", (data['devId'], data['name'], data['status'], data['power'], data['vol'], data['cat'], data['icon'], username, data['devId']))
        db.commit()
        refresh_device_session()
        app.logger.debug("Record successfully added %s", data)
        return json.dumps({'devId': data['devId'], 'name': data['name'], 'status': data['status'], 'power': data['power'], 'vol': data['vol'], 'cat': data['cat'], 'icon': data['icon']})
    except sql.Error as e:
        db.rollback()
        app.logger.debug("Database error: %s" % e)
    except Exception as e:
        db.rollback()
        app.logger.debug("Exception in _query: %s" % e)
    # finally:
    #     db.close()
    return ""

@app.route('/api/v1.0/device/<devId>', methods=['DELETE'])
def delete_device(devId):
    if not checkToken(request):
        app.logger.debug("Token is invalid")
        abort(404)
    try:
        username = session.get('username')
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM device WHERE devId=? AND username=?", (devId,username))
        row = cur.fetchone()
        if not row is None:
            app.logger.debug("Delete device %s %s" % (devId, username))
            cur.execute("DELETE FROM device WHERE devId=? AND username=?", (devId,username))
            db.commit()
            un_subscribe(devId)
            app.logger.debug("Record successfully deleted %s", devId)
            refresh_device_session()
            return devId
    except sql.Error as e:
        db.rollback()
        app.logger.debug("Database error: %s" % e)
    except Exception as e:
        db.rollback()
        app.logger.debug("Exception in _query: %s" % e)
    # finally:
    #     db.close()
    return ""

def checkHasKey(d, map):
    for k in map:
        if (k.split(" - ")[0] == d):
            return True
    return False

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', use_reloader=True, debug=True)