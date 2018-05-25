from flask import Flask
import json

app = Flask(__name__)
light_status = 'off'
valve_status = 'off'
fan_status = 'off'

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


@app.route('/')
def start():
    return 'IOT HOME PROJECT!'

@app.route('/api/v1.0/', methods=['GET'])
def api():
    return 'working'

@app.route('/api/v1.0/light', methods=['GET'])
def get_light_status():
    light_status = getStatus('light')
    if light_status is None:
        setStatus('light', 'off')
    return getStatus('light')

@app.route('/api/v1.0/light', methods=['POST'])
def post_light_status():
    light_status = getStatus('light')
    if light_status == "on":
        setStatus('light', 'off')
    else:
        setStatus('light', 'on')
    return getStatus('light')

@app.route('/api/v1.0/valve', methods=['GET'])
def get_valve_status():
    valve_status = getStatus('valve')
    if valve_status is None:
        setStatus('valve', 'off')
    return getStatus('valve')

@app.route('/api/v1.0/valve', methods=['POST'])
def post_valve_status():
    valve_status = getStatus('valve')
    if valve_status == "on":
        setStatus('valve', 'off')
    else:
        setStatus('valve', 'on')
    return getStatus('valve')

@app.route('/api/v1.0/fan', methods=['GET'])
def get_fan_status():
    fan_status = getStatus('fan')
    if fan_status is None:
        setStatus('fan', 'off')
    return getStatus('fan')

@app.route('/api/v1.0/fan', methods=['POST'])
def post_fan_status():
    fan_status = getStatus('fan')
    if fan_status == "on":
        setStatus('fan', 'off')
    else:
        setStatus('fan', 'on')
    return getStatus('fan')

@app.route('/api/v1.0/status', methods=['GET'])
def get_all_status():
    valve_status = getStatus('valve')
    light_status = getStatus('light')
    fan_status = getStatus('fan')
    return json.dumps({'valve': valve_status, 'light':light_status,'fan':  fan_status})

if __name__ == '__main__':

    app.run()
