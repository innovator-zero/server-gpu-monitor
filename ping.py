import json
import os
import time

import psutil
import pynvml
import requests
import yaml

with open(os.path.join(os.path.split(__file__)[0], 'config.yaml')) as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

client = config['client']
target = 'http://{}:{}/api/ping'.format(config['server']['ip'], config['server']['port'])

pynvml.nvmlInit()
gpu_nums = pynvml.nvmlDeviceGetCount()
handle_list = [pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(gpu_nums)]


def get_cpu_info():
    cpu_info = {}
    cpu_info['core'] = psutil.cpu_count(logical=False)  # number of cores
    cpu_info['thread'] = psutil.cpu_count()  # number of threads
    cpu_info['util'] = int(psutil.cpu_percent(percpu=False))
    cpu_info['temp'] = int(psutil.sensors_temperatures()['coretemp'][0].current)
    return cpu_info


def get_mem_info():
    mem_info = {}
    mem = psutil.virtual_memory()
    mem_total = float(mem.total) / 1024 / 1024 / 1024
    mem_used = float(mem.used) / 1024 / 1024 / 1024
    mem_info['status'] = '{:.2f}G/{:.2f}G'.format(mem_used, mem_total)
    mem_info['util'] = int(mem_used / mem_total * 100)
    return mem_info


def get_gpu_info():
    gpu_info = {}
    for i in range(len(handle_list)):
        vram_info = pynvml.nvmlDeviceGetMemoryInfo(handle_list[i])
        gpu_info[i] = {
            'name': str(pynvml.nvmlDeviceGetName(handle_list[i])),
            'gpu_util': int(pynvml.nvmlDeviceGetUtilizationRates(handle_list[i]).gpu),
            'vram_status': '{:d}M/{:d}M'.format(int(vram_info.used / 1024 / 1024), int(vram_info.total / 1024 / 1024)),
            'vram_util': int(vram_info.used / vram_info.total * 100),
            'temp': int(pynvml.nvmlDeviceGetTemperature(handle_list[i], 0))
        }
    return gpu_info


def is_useful_disk(mountpoint):
    blacklist = ['boot', 'var', 'snap']  # blacklist of path
    for name in blacklist:
        if name in mountpoint:
            return False
    return True


def get_disk_info():
    disk_info = {}
    for i in psutil.disk_partitions():
        if is_useful_disk(i.mountpoint):
            usage = psutil.disk_usage(i.mountpoint)
            d_total = int(usage.total / 1024 / 1024 / 1024)
            d_used = int(usage.used / 1024 / 1024 / 1024)
            disk_info[i.mountpoint] = {'status': '{:d}G/{:d}G'.format(d_used, d_total), 'util': usage.percent}
    disk_info = dict(sorted(disk_info.items()))
    return disk_info


def get_body():
    body = {'client': client, 'gpu_nums': gpu_nums, 'gpu_info': {}, 'time_stamp': None}
    body['cpu_info'] = get_cpu_info()
    body['mem_info'] = get_mem_info()
    body['gpu_info'] = get_gpu_info()
    body['disk_info'] = get_disk_info()
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

        time.sleep(2)  # update every 2 seconds
