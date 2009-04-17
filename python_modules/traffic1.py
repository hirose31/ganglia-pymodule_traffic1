#!/usr/bin/env python
# -*- coding: utf-8 -*-

descriptors = list()

PROC_FILE = "/proc/net/dev"
STATS_FOR = {
    "recv_bytes"  : 0,
    "recv_pkts"   : 1,
    "recv_errs"   : 2,
    "recv_drops"  : 3,
    "trans_bytes" : 8,
    "trans_pkts"  : 9,
    "trans_errs"  : 10,
    "trans_drops" : 11,
    }

def traffic_stats(name):
    type, target_device = name.rsplit("_",1)
    v = stats_of(target_device)
    if v:
        return int(v[ STATS_FOR[type] ])
    else:
        return -1

def stats_of(target_device):
    f = open(PROC_FILE, "r")
    for l in f:
        a = l.split(":")
        dev = a[0].lstrip()
        if dev != target_device:
            continue
        return a[1].split()
    return

def metric_init(params):
    global descriptors

    print '[traffic1] Received the following parameters'
    print params

    if "target_device" in params:
        target_device = params["target_device"]
    else:
        target_device = "lo"


    d0 = {
        'name'        : 'XXX',
        'call_back'   : traffic_stats,
        'time_max'    : 60,
        'value_type'  : 'uint',
        'units'       : 'XXX',
        'slope'       : 'positive',
        'format'      : '%d',
        'description' : 'XXX',
        'groups'      : 'network',
        }

    # IP:HOSTNAME
    if "spoof_host" in params:
        d0["spoof_host"] = params["spoof_host"]

    d = d0.copy()
    d["name"]        = 'trans_bytes_' + target_device
    d["units"]       = "bytes/sec"
    d["description"] = 'transmitted bytes per sec'
    descriptors.append(d)

    d = d0.copy()
    d["name"]        = 'recv_bytes_' + target_device
    d["units"]       = "bytes/sec"
    d["description"] = 'received bytes per sec'
    descriptors.append(d)

    return descriptors

def metric_cleanup():
    '''Clean up the metric module.'''
    pass

if __name__ == '__main__':
    params = {'target_device': "bond0"}
    metric_init(params)
    for d in descriptors:
        v = d['call_back'](d['name'])
        print 'value for %s is %d' % (d['name'], v)

