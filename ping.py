import json
import os
import time

import pynvml
import requests
import yaml

with open(os.path.join(os.path.split(__file__)[0], 'config.yaml')) as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

pynvml.nvmlInit()
host = config['host']
target = 'http://{}:{}/api/ping'.format(config['center']['ip'], config['center']['port'])
gpu_nums = pynvml.nvmlDeviceGetCount()
handle_list = [pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(gpu_nums)]


def get_gpu_info():
    gpu_info = {}
    for i in range(len(handle_list)):
        meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle_list[i])
        gpu_info[i] = {
            'name': str(pynvml.nvmlDeviceGetName(handle_list[i])),
            'gpu_util': int(pynvml.nvmlDeviceGetUtilizationRates(handle_list[i]).gpu),
            'vram_status': '{:d}M/{:d}M'.format(int(meminfo.used / 2**20), int(meminfo.total / 2**20)),
            'vram_util': int(meminfo.used / meminfo.total * 100)
        }
    return gpu_info


def get_body():
    body = {'host': host, 'gpu_nums': gpu_nums, 'gpu_info': {}, 'time_stamp': None}
    body['gpu_info'] = get_gpu_info()
    body['time_stamp'] = time.strftime("%Y-%m-%d %H:%M:%S")

    return body


if __name__ == "__main__":

    error_count = 0
    while True:
        body = get_body()
        success = False
        try:
            res = requests.post(target, json.dumps(body))
            if res.status_code == 200:
                success = True
                print('Success ping {:s}'.format(body['time_stamp']))
        except Exception as e:
            print(e)

        if not success:
            error_count += 1
            if error_count > 5:
                print('Failed to connect 5 times, try again in 3 minutes...')
                time.sleep(3 * 60)
                continue
        else:
            error_count = 0

        time.sleep(5)  # update every 5 seconds
