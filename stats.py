#!/bin/python2.7
# -*- coding: utf-8 -*-

import os, sys
import yaml,json
import logging, time
import requests
import psutil

EXIT_CODE=0
HOSTNAME = os.uname()[1]
CONFIG_FILE = "/etc/stats.yaml"
DATEFMT = '%Y-%m-%d %H:%M:%S'
LOG_FMT = "%(asctime)s %(levelname)-8.8s: %(message)s"

def process_exception(e, critical = False):
    global EXIT_CODE
    EXIT_CODE+=1
    if critical:
        logging.critical(e)
        sys.exit(EXIT_CODE)

    logging.warning(e)

def parse_config():
    with open(CONFIG_FILE) as config_file:
        try:
            return yaml.load(config_file)
        except Exception as e:
            process_exception(e, critical = True)

config = parse_config()

def now():
    return time.strftime(DATEFMT)

def b_to_mb(val):
    return float(val) / 2**20

# Returns used space fo mount points from config
def disks_stats():
    usages=[]
    if not config.get('disks', None):
        process_exception("config error: no section disk_usage. skip...")
        return usages

    if not config['disks'].get('mount_points', None):
        process_exception("config error: no section mount_points. skip...")
        return usages

    for mount_point in config['disks']['mount_points']:
        try:
            fs_stats = psutil.disk_usage(mount_point)
        except OSError as e:
            process_exception(e)
            continue
        used = b_to_mb(fs_stats.used)

        date = now()
        print "DISK date: %s mount_point: %s used: %s" % (date, mount_point, used, )
        usages.append({"date": date, "t":"DISK", "d1": HOSTNAME, "d2": mount_point, "V":used})

    return usages

def s_to_milliseconds(val):
    return int(val * 10**3)

# Returns iowait and user+sus times in milliseconds
def cpu_stats():
    cpu_times = psutil.cpu_times()
    user_system = s_to_milliseconds(cpu_times.user + cpu_times.system)
    iowait = s_to_milliseconds(cpu_times.iowait)

    date = now()
    print "CPU date: %s total: %s iowait: %s" % (date, user_system, iowait, )
    cpu_times = [
            {"date": date, "t": "CPU", "d1": HOSTNAME, "d2": "iowait", "V": iowait},
            {"date": date, "t": "CPU", "d1": HOSTNAME, "d2": "total",  "V": user_system},
            ]

    return cpu_times

def mem_stats():
    mem = psutil.virtual_memory()
    real_used = b_to_mb(mem.used - mem.buffers)
    swap_used = b_to_mb(psutil.swap_memory().used)

    date = now()
    print "MEM date: %s used: %s swap_used: %s" % (date, real_used, swap_used, )

    mem_stats = [
            {"date": date, "t": "MEM", "d1": HOSTNAME, "d2": "used", "V": real_used},
            {"date": date, "t": "MEM", "d1": HOSTNAME, "d2": "swap_used", "V": swap_used},
            ]

    return mem_stats

def network_stats():
    network_bytes = []
    if not config.get('networking', None):
        process_exception("config error: no section networking. skip...")
        return network_stats

    if not config['networking'].get('interfaces', None):
        process_exception("config error: no section interfaces. skip...")
        return network_stats

    counters = psutil.net_io_counters(True)
    for interface in config['networking']['interfaces']:
        counter = counters.get(interface, None)
        if not counter:
            process_exception('cannot find counters for interface %s. skip..' % interface)
            continue

        date = now()
        print "NET date: %s interface: %s recv: %s sent: %s" % (date, interface, counter.bytes_recv, counter.bytes_sent, )
        network_bytes.extend([
                {"date": date, "t": "NET", "d1": HOSTNAME, "d2": "%s_recv" % interface, "V": counter.bytes_recv},
                {"date": date, "t": "NET", "d1": HOSTNAME, "d2": "%s_sent" % interface, "V": counter.bytes_sent},
                ])

    return network_bytes

def io_stats():
    io_perdev = []
    if not config.get('disks', None):
        process_exception("config error: no section disks. skip...")
        return io_perdev

    if not config['disks'].get('block_devs', None):
        process_exception("config error: no section block_devs. skip...")
        return io_perdev

    counters = psutil.disk_io_counters(perdisk=True)
    for dev in config['disks']['block_devs']:
        counter = counters.get(dev, None)
        if not counter:
            process_exception('cannot find counters for block device %s. skip..' % dev)
            continue

        date = now()
        print "DISK date: %s block_dev: %s reads: %s writes: %s" % (date, dev, counter.read_count, counter.write_count, )
        io_perdev.extend([
               {"date": date, "t": "DISK", "d1": HOSTNAME, "d2": "%s_reads" % dev, "V": counter.read_count},
               {"date": date, "t": "DISK", "d1": HOSTNAME, "d2": "%s_writes" % dev, "V": counter.write_count},
               ])

    return io_perdev




def main():
    stats = disks_stats() + cpu_stats() + mem_stats() + network_stats() + io_stats()

    if not config.get('api_url', None):
        process_exception("config error: no api_url in config", critical = True)

    if not config.get('api_key', None):
        process_exception("config error: no api_key in config", critical = True)

    json_data = json.dumps({
            "apiKey":  config['api_key'],
            "records": stats
            })

    resp = requests.post(config['api_url'], data = {'json': json_data})
    if resp.json()['status'] == 'ERROR':
        process_exception("Error while sending data status: %(status)s errorDetails: %(errorDetails)s" % resp.json(), critical = True)


    sys.exit(EXIT_CODE if EXIT_CODE < 256 else 255)


if __name__ == "__main__":
    logging.basicConfig(format = LOG_FMT, level = logging.INFO, datefmt = DATEFMT)
    main()
