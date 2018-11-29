# App will load job from db and add to schedule
# First iml: will reload every day to refresh job which CRUD from api
# Advance: will listen mqtt to modify current job
import json
import time
import os
import sqlite3 as sql
import schedule
import configparser
import paho.mqtt.client as mqtt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "../iot.db")

config = configparser.ConfigParser()
config.read('config.ini')

class IOTJob:
    def __init__(self, debug=0, db=None):
        self.debug = debug
        self.schedule = schedule
        self.db = db

    def log_msg(self, msg, level=None):
        tstr = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(time.time()))
        if level is None:
            level = self.debug
        if level > 0:
            print("%s - %s" % (tstr, msg))

    def loadjobs(self):
        self.log_msg("Load JOBS from DB ...")
        cur = self.db.cursor()
        cur.execute("SELECT * FROM timer")
        rows = cur.fetchall()
        for row in rows:
            self.schedulejob(row[0], row[1], row[2], row[3], row[4])
        return True

    def schedulejob(self, devid, timer, period, at, action):
        createjob(devid, timer, period, at, action)
        return "OK"

    def run_schedule(self):
        while 1:
            self.schedule.run_pending()
            time.sleep(1)

    def run(self):
        rc = 0
        try:
            # if not self.schedulejob():
            #     rc = 3
            if self.loadjobs():
                self.run_schedule()
                time.sleep(10)
        except Exception as e:
            self.log_msg(str(e), 2)
            rc = 2
        return rc

def app_msg(msg):
    tstr = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(time.time()))
    print("%s - %s" % (tstr, msg))

def iotjob(devid, action):
    topic = "cmnd/{}/power".format(devid)
    status = 'off' if action == 0 else 'on' if action == 1 else 'toggle'
    app_msg("publish job: '%s' '%s" % (topic, status))
    # client.publish(topic, status, 2)

def createjob(devid, timer, period, at, action):
    job = schedule.every()
    if period == 'day':
        job = job.day
    elif period == 'hour':
        job = job.hour
    elif period == 'minute':
        job = job.minute
    elif period == 'second':
        job = job.second
    else:
        return "Invalid period " + period
    if at != '':
        job = job.at(at)
    tag = '-'.join([devid, str(timer)])
    job.do(iotjob, devid, action).tag(tag)
    return job

def getdb():
    try:
        db = sql.connect(DATABASE)
        return db
    except sql.Error as e:
        app_msg(e)
    return None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")
        global Connected                #Use global variable
        Connected = True                #Signal connection
        client.subscribe("topic/schedule", 2)
    else:
        app_msg("Connection failed")

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    if not data is None:
        if data["type"] == "ADD":
            app_msg("CREATE A JOB FROM API")
            createjob(data['devId'], data['timer'],data['period'], data['at'], data['action'])
        elif data["type"] == "REPLACE":
            app_msg("REPLACE A JOB FROM API")
            tag = '-'.join([data['devId'], str(data['timer'])])
            schedule.clear(tag)
            createjob(data['devId'], data['timer'],data['period'], data['at'], data['action'])
        else:
            app_msg("REMOVE A JOB FROM API")
            tag = '-'.join([data['devId'], str(data['timer'])])
            schedule.clear(tag)

def main(argv=None):
    debug =1
    db = getdb()
    job = IOTJob(debug, db)
    job.run()

Connected = False
client = mqtt.Client('scheduler')
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set(config['DEFAULT']['MQTT_USERNAME'], config['DEFAULT']['MQTT_PASSWORD'])
client.connect(config['DEFAULT']['MQTT_BROKER_URL'] ,1883, 60)

client.loop_start()

while Connected != True:    #Wait for connection
    time.sleep(0.1)

if __name__ == "__main__":
    try:
        while True:
            main()

    except KeyboardInterrupt:
        app_msg("exiting")
        client.disconnect()
        client.loop_stop()
