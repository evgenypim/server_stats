#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, subprocess
import common

def dirs_size():
    sizes = []
    if not common.check_config_sections(['disks', 'dirs_size']):
        return sizes

    for directory in common.config['disks']['dirs_size']:
        if not os.path.exists(directory):
            common.process_exception("%s is not exists. skip..." % directory )

        cmd="du -s %s" % directory
        size=subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True).\
                communicate()[0].split()[0]
        size = common.kb_to_mb(size)
        date = common.now()
        print "DSIZE date: %s directory: %s size: %s" % (date, directory, size, )
        sizes.append({"date": date, "t":"DSIZE", "d1": common.HOSTNAME, "d2": directory, "V":size})

    return sizes

def main():
    stats = dirs_size() 

    common.check_config_sections(['api_url',], critical=True)
    common.check_config_sections(['api_key',], critical=True)

    common.send_stats(stats)

    exit(common.EXIT_CODE if common.EXIT_CODE < 256 else 255)

if __name__ == "__main__":
    main()
