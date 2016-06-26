#!/usr/bin/env python

import os, sys
import yaml,json
import logging, time
import requests
import subprocess

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

def kb_to_mb(val):
    return float(val) / 2**10

def dirs_size():
    sizes = []
    if not config.get('disks', None):
        process_exception("config error: no section disks. skip...")
        return sizes

    if not config['disks'].get('dirs_size', None):
        process_exception("config error: no section dirs_size. skip...")
        return sizes

    for directory in config['disks']['dirs_size']:
        if not os.path.exists(directory):
            process_exception("%s is not exists. skip..." % directory )

        cmd="du -s %s" % directory
        size=subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True).\
                communicate()[0].split()[0]
        size = kb_to_mb(size)
        date = now()
        print "DSIZE date: %s directory: %s size: %s" % (date, directory, size, )
        sizes.append({"date": date, "t":"DSIZE", "d1": HOSTNAME, "d2": directory, "V":size})

    return sizes

def main():
    stats = dirs_size() 

    if not config.get('api_url', None):
        process_exception("config error: no api_url in config", critical = True)

    if not config.get('api_key', None):
        process_exception("config error: no api_key in config", critical = True)

    json_data = json.dumps({
            "apiKey":  config['api_key'],
            "records": stats
            })
    date = now()
    print "API request date: %s  json %s" % (date, json_data, )

    resp = requests.post(config['api_url'], data = {'json': json_data})
    if resp.status_code != 200:
        process_exception("API responded with non 200 status. code: %s body: %s" %(resp.status_code, resp.text), critical = True)

    if resp.json()['status'] == 'ERROR':
        process_exception("Error while sending data status: %(status)s errorDetails: %(errorDetails)s" % resp.json(), critical = True)

    sys.exit(EXIT_CODE if EXIT_CODE < 256 else 255)

if __name__ == "__main__":
    logging.basicConfig(format = LOG_FMT, level = logging.INFO, datefmt = DATEFMT)
    main()
