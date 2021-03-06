#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os, time, sys
import yaml, json
import requests

EXIT_CODE=0
HOSTNAME = os.uname()[1]
CONFIG_FILE = "/etc/stats.yaml"
DATEFMT = '%Y-%m-%d %H:%M:%S'
LOG_FMT = "%(asctime)s %(levelname)-8.8s: %(message)s"
DATA_DIR = '/var/stats_data'

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

# returns last_start_time
# returns 0 if LSAT_START_FILE is not exists
def touch_last_start_file(prefix=''):
    file_name = "%s.%s" % (prefix, 'last_start')
    last_start_path = os.path.join(DATA_DIR, file_name)
    last_start_time = 0
    if os.path.exists(last_start_path):
        last_start_time = os.path.getmtime(last_start_path)

    open(last_start_path, 'w').close()
    return last_start_time

def now():
    return time.strftime(DATEFMT)

def b_to_mb(val):
    return float(val) / 2**20

def kb_to_mb(val):
    return float(val) / 2**10

def s_to_milliseconds(val):
    return int(val * 10**3)

def send_stats(stats={}):
    json_data = json.dumps({
            "apiKey":  config['api_key'],
            "records": stats
            })
    date = now()
    print "API request date: %s json %s" % (date, json_data, )

    resp = requests.post(config['api_url'], data = {'json': json_data})
    if resp.status_code != 200:
        process_exception("API responded with non 200 status. code: %s body: %s" %(resp.status_code, resp.text), critical = True)

    if resp.json()['status'] == 'ERROR':
        process_exception("Error while sending data status: %(status)s errorDetails: %(errorDetails)s" % resp.json(), critical = True)

def check_config_sections(sections=[], critical=False):
    section=config
    for section_name in sections:
        section = section.get(section_name, None)
        if not section:
            process_exception("config error: no section %s." % section_name, critical = critical)
            return False

    return True

logging.basicConfig(format = LOG_FMT, level = logging.INFO, datefmt = DATEFMT)
config = parse_config()

if not os.path.exists(DATA_DIR):
    try:
        os.makedirs(DATA_DIR)
    except OSError as e:
        process_exception(e, critical = True)

if not os.path.isdir(DATA_DIR):
    process_exception("%s is not directory" % DATA_DIR, critical = True)
