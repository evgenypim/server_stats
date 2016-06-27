#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psutil
import common

# Returns used space for mount points from config
def disks_stats():
    usages=[]
    if not common.check_config_sections(['disks', 'mount_points']):
        return usages

    for mount_point in common.config['disks']['mount_points']:
        try:
            fs_stats = psutil.disk_usage(mount_point)
        except OSError as e:
            common.process_exception(e)
            continue
        used = common.b_to_mb(fs_stats.used)

        date = common.now()
        print "DISK date: %s mount_point: %s used: %s" % (date, mount_point, used, )
        usages.append({"date": date, "t":"DISK", "d1": common.HOSTNAME, "d2": mount_point, "V":used})

    return usages

# Returns iowait and user+sus times in milliseconds
def cpu_stats():
    cpu_times = psutil.cpu_times()
    user_system = common.s_to_milliseconds(cpu_times.user + cpu_times.system)
    iowait = common.s_to_milliseconds(cpu_times.iowait)

    date = common.now()
    print "CPU date: %s total: %s iowait: %s" % (date, user_system, iowait, )
    cpu_times = [
            {"date": date, "t": "CPU", "d1": common.HOSTNAME, "d2": "iowait", "V": iowait},
            {"date": date, "t": "CPU", "d1": common.HOSTNAME, "d2": "total",  "V": user_system},
            ]

    return cpu_times

def mem_stats():
    mem = psutil.virtual_memory()
    real_used = common.b_to_mb(mem.used - mem.buffers)
    swap_used = common.b_to_mb(psutil.swap_memory().used)

    date = common.now()
    print "MEM date: %s used: %s swap_used: %s" % (date, real_used, swap_used, )

    mem_stats = [
            {"date": date, "t": "MEM", "d1": common.HOSTNAME, "d2": "used", "V": real_used},
            {"date": date, "t": "MEM", "d1": common.HOSTNAME, "d2": "swap_used", "V": swap_used},
            ]

    return mem_stats

def network_stats():
    network_bytes = []
    if not common.check_config_sections(['networking', 'interfaces']):
        return network_bytes

    counters = psutil.net_io_counters(True)
    for interface in common.config['networking']['interfaces']:
        counter = counters.get(interface, None)
        if not counter:
            common.process_exception('cannot find counters for interface %s. skip..' % interface)
            continue

        date = common.now()
        print "NET date: %s interface: %s recv: %s sent: %s" % (date, interface, counter.bytes_recv, counter.bytes_sent, )
        network_bytes.extend([
                {"date": date, "t": "NET", "d1": common.HOSTNAME, "d2": interface, "d3": "recv", "V": counter.bytes_recv},
                {"date": date, "t": "NET", "d1": common.HOSTNAME, "d2": interface, "d3": "sent", "V": counter.bytes_sent},
                ])

    return network_bytes

def io_stats():
    io_perdev = []
    if not common.check_config_sections(['disks', 'block_devs']):
        return io_perdev

    counters = psutil.disk_io_counters(perdisk=True)
    for dev in common.config['disks']['block_devs']:
        counter = counters.get(dev, None)
        if not counter:
            common.process_exception('cannot find counters for block device %s. skip..' % dev)
            continue

        date = common.now()
        print "DISK date: %s block_dev: %s reads: %s writes: %s" % (date, dev, counter.read_count, counter.write_count, )
        io_perdev.extend([
               {"date": date, "t": "DISK", "d1": common.HOSTNAME, "d2": dev, "d3": "reads", "V": counter.read_count},
               {"date": date, "t": "DISK", "d1": common.HOSTNAME, "d2": dev, "d3": "writes", "V": counter.write_count},
               ])

    return io_perdev

def main():
    stats = disks_stats() + cpu_stats() + mem_stats() + network_stats() + io_stats()

    common.check_config_sections(['api_url',], critical=True)
    common.check_config_sections(['api_key',], critical=True)

    common.send_stats(stats)
    exit(common.EXIT_CODE if common.EXIT_CODE < 256 else 255)

if __name__ == "__main__":
    main()
