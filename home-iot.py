from flask import Flask, g

app = Flask(__name__)
status = 'off'

def getStatus():
    global status
    return status

def setStatus(v):
    global status
    status = v

@app.route('/')
def start():
    return 'IOT HOME PROJECT!'

@app.route('/api/v1.0/light', methods=['GET'])
def get_light_status():
    status = getStatus()
    if status is None:
        setStatus('off')
    return getStatus()

@app.route('/api/v1.0/light', methods=['POST'])
def post_light_status():
    status = getStatus()
    if status == "on":
        setStatus('off')
    else:
        setStatus('on')
    return getStatus()

if __name__ == '__main__':

    app.run()
