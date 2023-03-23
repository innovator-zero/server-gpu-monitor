import json
import os
import socket
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


def get_host_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        return ip


def get_gpu_info():
    gpu_info = {}
    for i in range(len(handle_list)):
        meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle_list[i])
        gpu_info[i] = {
            'name': pynvml.nvmlDeviceGetName(handle_list[i]),
            'gpu_util': pynvml.nvmlDeviceGetUtilizationRates(handle_list[i]).gpu,
            'vram_status': '{:d}M/{:d}M'.format(int(meminfo.used / 2**20), int(meminfo.total / 2**20)),
            'vram_util': round(meminfo.used / meminfo.total * 100)
        }
    return gpu_info


if __name__ == "__main__":
    body = {'host': host, 'gpu_nums': gpu_nums, 'gpu_info': {}, '_date': None}
    error_count = 0
    while True:
        # body['ip'] = get_host_ip()
        body['gpu_info'] = get_gpu_info()
        body['time_stamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
        success = False
        try:
            res = requests.post(target, json.dumps(body))
            if res.status_code == 200:
                success = True
                print('Success ping {:s}'.format(body['time_stamp']))
        except Exception:
            pass

        if not success:
            error_count += 1
            if error_count > 5:
                print('Failed to connect 5 times, try again in 3 minutes...')
                time.sleep(3 * 60)
                continue
        else:
            error_count = 0

        time.sleep(5)  # update every 5 seconds
