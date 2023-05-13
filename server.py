import json
import os
import time

import yaml
from flask import Flask, request, send_file

from ping import get_body

with open(os.path.join(os.path.split(__file__)[0], 'config.yaml')) as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

app = Flask(__name__)

act_map = {}

client = config['client']


@app.route('/')
def index():
    return send_file('templates/index.html')


@app.route('/api/monitor', methods=['GET'])
def monitor():
    # get itself info
    global act_map
    act_map[client] = get_body()
    if act_map:
        for key, value in act_map.items():
            time_str = value['time_stamp']
            time_stamp = time.mktime(time.strptime(time_str, "%Y-%m-%d %H:%M:%S"))
            # disconnect over 1 minute
            if time.time() - time_stamp > 60:
                value['status'] = 'OFFLINE'
            else:
                value['status'] = 'ONLINE'

        act_map = dict(sorted(act_map.items()))
    return json.dumps(act_map)


@app.route('/api/ping', methods=['GET', 'POST'])
def ping():
    body = 0
    if request.method == 'POST':
        data = request.get_data()
        data = json.loads(data.decode())
        if not data.get('client'):
            body = 1
        else:
            act_map[data['client']] = data
    return str(body)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(config['center']['port']))
