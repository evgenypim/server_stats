#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os, glob, re 
import common
LAST_START_TIME = common.touch_last_start_file(prefix='log_parser')

def get_response_time(line='', url_regex=None):
    splited = line.split()
    url = splited[11].split('?')[0]

    if url_regex:
        if not url_regex.search(url):
            return None

    return float(splited[9].replace('ms', ''))

def process_logs(log_name_pattern, url_regex=None):
    response_times = []
    for log_path in glob.glob(log_name_pattern):
        if os.path.getmtime(log_path) < LAST_START_TIME: 
            continue
    
        log_name = os.path.basename(log_path)
        shift_file_path = os.path.join(common.DATA_DIR, log_name)
    
        shift = 0
        if os.path.exists(shift_file_path):
            try:
                with open(shift_file_path, 'r') as shift_file:
                    shift = int(shift_file.read())
            except IOError as e:
                common.process_exception(e, critical = True)
        
        try:
            with open(log_path, 'r') as apache_log:
                apache_log.seek(shift, 0)
                for line in apache_log:
                    response_time = get_response_time(line, url_regex)
                    if response_time != None:
                        response_times.append(response_time)
        
                shift = apache_log.tell()

            with open(shift_file_path, 'w') as shift_file:
                shift_file.write(str(shift))

        except IOError as e:
            common.process_exception(e, critical = True)
        
    count = len(response_times)
    avg_time = sum(response_times) / count if count > 0 else 0

    return (count, avg_time)

def apache_stats():
    apache_logs_stats = []

    if not common.check_config_sections(['apache_logs',]):
        return apache_logs_stats

    for website in common.config['apache_logs']:
        website_name = website.keys()[0]
        website_config = website.values()[0]
        log_file_pattern = website_config.get('file', None)
        if not log_file_pattern:
            common.process_exception("no logfile pattern for website %s" % website)

        url_filter_string = website_config.get('url_filter', None)
        url_regex = re.compile(url_filter_string) if url_filter_string else None

        count, avg_time = process_logs(log_file_pattern, url_regex)

        date = common.now()
        print "LOGS date: %s website: %s count: %s duration: %s" % (date, website_name, count, avg_time)
        apache_logs_stats.extend([
            {'date': date, 't': 'LOG_REQUESTS-COUNT', 'd1': common.HOSTNAME, 'd2': website_name, 'v': count},
            {'date': date, 't': 'LOG_REQUESTS-DURATION', 'd1': common.HOSTNAME, 'd2': website_name, 'v': avg_time},
        ])

    return apache_logs_stats

def main():
    stats = apache_stats()

    common.check_config_sections(['api_url',], critical=True)
    common.check_config_sections(['api_key',], critical=True)

    common.send_stats(stats)
    exit(common.EXIT_CODE if common.EXIT_CODE < 256 else 255)

if __name__ == "__main__":
    main()
