#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import threading
import time

descriptors = list()
Desc_Skel   = {}
_Worker_Thread = None
_Lock = threading.Lock() # synchronization lock

class UpdateTrafficThread(threading.Thread):
    '''update traffic'''

    __slots__ = ( 'proc_file' )

    def __init__(self, params):
        threading.Thread.__init__(self)
        self.running       = False
        self.shuttingdown  = False
        self.target_device = params["target_device"]
        self.refresh_rate  = int(params["refresh_rate"])
        self.proc_file = "/proc/net/dev"
        self.stats_tab = {
            "recv_bytes"  : 0,
            "recv_pkts"   : 1,
            "recv_errs"   : 2,
            "recv_drops"  : 3,
            "trans_bytes" : 8,
            "trans_pkts"  : 9,
            "trans_errs"  : 10,
            "trans_drops" : 11,
            }
        self.stats         = {}

    def shutdown(self):
        self.shuttingdown = True
        if not self.running:
            return
        self.join()

    def run(self):
        self.running = True

        while not self.shuttingdown:
            _Lock.acquire()
            self.update_stats()
            _Lock.release()

            time.sleep(self.refresh_rate)

        self.running = False

    def update_stats(self):
        f = open(self.proc_file, "r")
        for l in f:
            a = l.split(":")
            dev = a[0].lstrip()
            if dev == self.target_device:
                _stats = a[1].split()
                for name, index in self.stats_tab.iteritems():
                    self.stats[name+'_'+self.target_device] = int(_stats[index])
                break
        return

    def stats_of(self, name):
        val = 0
        if name in self.stats:
            _Lock.acquire()
            val = self.stats[name]
            _Lock.release()
        return val

def create_desc(prop):
    d = Desc_Skel.copy()
    for k,v in prop.iteritems():
        d[k] = v
    return d

def traffic_stats(name):
    return _Worker_Thread.stats_of(name)

def metric_init(params):
    global descriptors, Desc_Skel, _Worker_Thread

    print '[traffic1] Received the following parameters'
    print params

    Desc_Skel = {
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

    if "refresh_rate" not in params:
        params["refresh_rate"] = 10
    if "target_device" not in params:
        params["target_device"] = "lo"
    target_device = params["target_device"]

    _Worker_Thread = UpdateTrafficThread(params)
    _Worker_Thread.start()

    # IP:HOSTNAME
    if "spoof_host" in params:
        Desc_Skel["spoof_host"] = params["spoof_host"]

    descriptors.append( create_desc({
                "name"        : 'recv_bytes_' + target_device,
                "units"       : "bytes/sec",
                "description" : 'received bytes per sec',
                }) )
    descriptors.append( create_desc({
                "name"        : 'recv_pkts_' + target_device,
                "units"       : "pkts/sec",
                "description" : 'received packets per sec',
                }) )
    descriptors.append( create_desc({
                "name"        : 'recv_errs_' + target_device,
                "units"       : "pkts/sec",
                "description" : 'received error packets per sec',
                }) )

    descriptors.append( create_desc({
                "name"        : 'trans_bytes_' + target_device,
                "units"       : "bytes/sec",
                "description" : 'transmitted bytes per sec',
                }) )
    descriptors.append( create_desc({
                "name"        : 'trans_pkts_' + target_device,
                "units"       : "pkts/sec",
                "description" : 'transmitted packets per sec',
                }) )
    descriptors.append( create_desc({
                "name"        : 'trans_errs_' + target_device,
                "units"       : "pkts/sec",
                "description" : 'transmitted error packets per sec',
                }) )

    return descriptors

def metric_cleanup():
    '''Clean up the metric module.'''
    _Worker_Thread.shutdown()

if __name__ == '__main__':
    try:
        params = {'target_device': "eth0"}
        metric_init(params)
        while True:
            for d in descriptors:
                v = d['call_back'](d['name'])
                print 'value for %s is %d' % (d['name'], v)
            time.sleep(5)
    except KeyboardInterrupt:
        time.sleep(0.2)
        os._exit(1)
