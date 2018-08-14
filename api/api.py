import datetime
import json
from flask import Blueprint

api = Blueprint(name='api', import_name=__name__, url_prefix='/api')

light_status = 'off'
valve_status = 'off'
fan_status = 'off'
timestamp = datetime.datetime.now().time()
mode = 'AUTO'


def getStatus(type):
    global light_status
    global valve_status
    global fan_status
    if(type == 'light'):
        return light_status
    if(type == 'valve'):
        return valve_status
    if(type == 'fan'):
        return fan_status

def setStatus(type, value):
    global light_status
    global valve_status
    global fan_status
    if(type == 'light'):
        light_status = value
    if(type == 'valve'):
        valve_status = value
    if(type == 'fan'):
        fan_status = value

def getMode():
    global mode
    return mode

def setMode(v):
    global mode
    mode = v

def warteringTime():
    if (mode == 'AUTO'):
        print("Wartering at %s" % (timestamp))
        return datetime.time(hour=11, minute=20) <= timestamp <= datetime.time(hour=11, minute=30) or \
               datetime.time(hour=20, minute=0) <= timestamp <= datetime.time(hour=20, minute=10)
    else:
        return False

@api.route('/v1.0/', methods=['GET'])
def status():
    return 'working'

@api.route('/v1.0/light', methods=['GET'])
def get_light_status():
    light_status = getStatus('light')
    if light_status is None:
        setStatus('light', 'off')
    return getStatus('light')

@api.route('/v1.0/light', methods=['POST'])
def post_light_status():
    light_status = getStatus('light')
    if light_status == "on":
        setStatus('light', 'off')
    else:
        setStatus('light', 'on')
    return getStatus('light')

@api.route('/v1.0/valve', methods=['GET'])
def get_valve_status():
    if warteringTime():
        valve_status = 'on'
        return valve_status
    valve_status = getStatus('valve')
    if valve_status is None:
        setStatus('valve', 'off')
    return getStatus('valve')

@api.route('/v1.0/valve', methods=['POST'])
def post_valve_status():
    valve_status = getStatus('valve')
    if valve_status == "on":
        setStatus('valve', 'off')
    else:
        setStatus('valve', 'on')
    return getStatus('valve')

@api.route('/v1.0/fan', methods=['GET'])
def get_fan_status():
    fan_status = getStatus('fan')
    if fan_status is None:
        setStatus('fan', 'off')
    return getStatus('fan')

@api.route('/v1.0/fan', methods=['POST'])
def post_fan_status():
    fan_status = getStatus('fan')
    if fan_status == "on":
        setStatus('fan', 'off')
    else:
        setStatus('fan', 'on')
    return getStatus('fan')

@api.route('/v1.0/status', methods=['GET'])
def get_all_status():
    valve_status = getStatus('valve')
    light_status = getStatus('light')
    fan_status = getStatus('fan')
    return json.dumps({'valve': valve_status, 'light':light_status,'fan':  fan_status})

@api.route('/v1.0/mode', methods=['POST'])
def post_mode():
    if getMode() == 'AUTO':
        setMode('MANUAL')
    else:
        setMode('AUTO')
    return mode

@api.route('/v1.0/mode', methods=['GET'])
def get_mode():
    mode = getMode()
    if mode is None:
        setMode('MANUAL')
    return getMode()