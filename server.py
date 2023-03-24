import json
import os
import time

import yaml
import pynvml
from flask import Flask, request, send_file
from ping import get_body

with open(os.path.join(os.path.split(__file__)[0], 'config.yaml')) as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

app = Flask(__name__)

act_map = {}

pynvml.nvmlInit()
host = config['host']
gpu_nums = pynvml.nvmlDeviceGetCount()
handle_list = [pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(gpu_nums)]


@app.route('/')
def index():
    return send_file('templates/index.html')


@app.route('/api/gpu', methods=['GET'])
def gpu():
    global act_map
    # get info of itself
    act_map[host] = get_body()

    # check whether info is valid
    if act_map:
        for key, value in act_map.items():
            time_str = value['time_stamp']
            time_stamp = time.mktime(time.strptime(time_str, "%Y-%m-%d %H:%M:%S"))
            # disconnect over 1 minute
            if time.time() - time_stamp > 60:
                del value['gpu_info']

        act_map = dict(sorted(act_map.items()))
    return json.dumps(act_map)


@app.route('/api/ping', methods=['GET', 'POST'])
def ping():
    body = 0
    if request.method == 'POST':
        data = request.get_data()
        data = json.loads(data.decode())
        if not data.get('host'):
            body = 1
        else:
            act_map[data['host']] = data
    return str(body)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(config['center']['port']))
