import datetime
import subprocess
import os
import time
import urllib2
from collections import OrderedDict
from math import floor, log

import psutil


def convert_bytes(value, unit, output_str=False, decimals=2, auto_determine=False):
    """

    :param value: int
    :param unit: str
    :param output_str: bool
    :param decimals: int
    :param auto_determine: bool
    :return: str or int or float
    """
    assert any([type(value) == int, type(value) == float, type(value) is long])
    assert all([type(decimals) is int, type(output_str) is bool, type(auto_determine) is bool, value >= 0])
    conversions = dict(B=0, KB=1, MB=2, GB=3, TB=4, PB=5, EB=6, ZB=7, YB=8)
    assert unit in conversions
    base = 1024.0
    converted_value = float(value) / base ** conversions[unit]
    if auto_determine and value > 0:
        # Generate automatic prefix by bytes
        base_power = floor(log(float(value)) / log(base))
        swap_conversion_values = {conversions[x]: x for x in conversions}
        while base_power not in swap_conversion_values:
            # future proofing. Not really necessary.
            base_power -= base_power
        unit = swap_conversion_values[base_power]
        converted_value = value / base ** conversions[unit]
    if output_str:
        if decimals < 0:
            decimals = 0
        return '{:,.{decimal}f} {unit}'.format(converted_value, decimal=decimals, unit=unit)
    else:
        return converted_value


def get_wan_ip(site='http://myip.dnsdynamic.org/'):
    return urllib2.urlopen(site).read()


def get_partitions():
    partitions = psutil.disk_partitions(all=True)
    return {p[1]: psutil.disk_usage(p[1]) for p in partitions if p[0] != 0}


def get_ping(host="8.8.8.8", kind='avg', num=4):
    # solution from http://stackoverflow.com/questions/316866/ping-a-site-in-python
    """
    returns ping time to selected site
        host: site, ip address to ping
        kind:
        num: number of pings to host

    :param host: string
    :param kind: string
    :param num: int
    :return: float
    """
    assert kind in ['max', 'avg', 'mdev', 'min']
    assert type(int(num)) is int
    ping = subprocess.Popen(["ping", "-c", str(num), host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, error = ping.communicate()
    out = out.split('\n')
    try:
        out = [x for x in out if x.startswith('rtt')][0]
        out_mapped = zip(out.split()[1].split('/'), out.split()[3].split('/'))
        out_mapped = {x[0]: x[1] for x in out_mapped}
        out = out_mapped[kind]
    except IndexError:
        # most likely no ping returned, system offline
        out = 0
    return float(out)


def get_system_uptime():
    def append_type(x, kind):
        """
        Return 0 if days/hours/minutes equals 0 otherwise append correct plural "s" to type
        ex. if systems up for 2 hours, returns "2 hours" likewise return "1 hour" if system has been up for 1 hour
        """
        assert type(x) is int and type(kind) is str
        if x == 0:
            return x
        else:
            return '{} {}'.format(str(x), kind + 's' if x != 1 else kind)

    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).replace(microsecond=0)
    time_now = datetime.datetime.now().replace(microsecond=0)
    delta = time_now - boot_time
    formatted_time = str(delta).split(',')
    try:
        # System's been up a day or more
        hours = formatted_time[1].strip().split(':')
    except IndexError:
        # System's been up for less than day
        hours = formatted_time[0].strip().split(':')
        formatted_time[0] = 0
    hours.pop(2)
    hours, mins = [int(hour) for hour in hours]
    formatted_time = dict(days=formatted_time[0], hours=append_type(hours, 'hour'), min=append_type(mins, 'minute'))
    output = dict(
        boottime=boot_time,
        uptime=delta,
        uptime_formatted=formatted_time)
    return output


def return_network_io():
    """
    returns Network bytes sent, and received
    :rtype : list
    """
    network_io = psutil.net_io_counters()
    return [network_io.bytes_sent, network_io.bytes_recv]


def get_network_speed(sleep=1):
    assert type(sleep) is int
    start_time = datetime.datetime.now()
    start_data = return_network_io()
    time.sleep(sleep)
    time_delta = datetime.datetime.now() - start_time
    end_data = return_network_io()
    bits = 8
    return dict(up=convert_bytes((end_data[0] - start_data[0]) / time_delta.seconds * bits, 'MB'),
                down=convert_bytes((end_data[1] - start_data[1]) / time_delta.seconds * bits, 'MB'))


def get_total_system_space(digits=1):
    """
    returns total system disk space formatted, ex.
        {'total': '8,781.9 GB', 'used': '3,023.0 GB', 'pct': 34.4, 'free': '5,313.4 GB'}

    :rtype : dict
    :param digits: int
    :return: dict
    """
    assert type(digits) is int
    partitions = get_partitions()
    disk_space = dict(total=sum([partitions[partition].total for partition in partitions]),
                      used=sum([partitions[partition].used for partition in partitions]),
                      free=sum([partitions[partition].free for partition in partitions]))
    disk_space_formatted = {k: convert_bytes(disk_space[k], 'GB', True, digits, True) for k in disk_space}
    disk_space_formatted['pct'] = round(float(disk_space['used']) / float(disk_space['total']) * 100.0, digits)
    return disk_space_formatted


def get_partitions_space(partitions, digits=1, sort='alpha'):
    """
    {'Home': {'total': '168.8 GB', 'pct': 44.4, 'free': '85.3 GB', 'used': '74.9 GB'},
        'Incoming': {'total': '293.3 GB', 'pct': 48.2, 'free': '137.0 GB', 'used': '141.4 GB'}}
    :param partitions:
    :param digits:
    :return:
    """
    assert type(partitions) is dict
    system_partitions = get_partitions()
    disk_space = {p: system_partitions[partitions[p]] for p in partitions}
    disk_space_formatted = {p: dict(total=convert_bytes(disk_space[p].total, 'GB', True, digits, True),
                                    used=convert_bytes(disk_space[p].used, 'GB', True, digits, True),
                                    free=convert_bytes(disk_space[p].free, 'GB', True, digits, True)) for p in
                            disk_space}
    for p in disk_space:
        disk_space_formatted[p]['pct'] = round(float(disk_space[p].used) / float(disk_space[p].total) * 100.0,
                                               digits)
    if sort.lower() == 'alpha':
        # place in ordered dictionary so paths always display in alphabetical order on page
        disk_space_formatted = OrderedDict(sorted(disk_space_formatted.items(), key=lambda x: x[0]))
    return disk_space_formatted


class GetSystemInfo(object):
    def __init__(self):
        pass

    def get_info(self):
        """
        Returns system information in a dictionary
            mem_total: Total RAM in the system in megabytes as float, ex. "7876.88671875"
            mem_available: Unused RAM in the system in megabytes as float, ex. "4623.8671875"
            mem_used_pct: mem_available / mem_total as float, ex. "41.3"
            load_avg: tuple of avg loads at 1 min, 5 min, and 15 min, respectively, ex. "(0.52, 0.51, 0.43)"
            partitions: dictionary of partitions on system, truncated ex, {''/mnt/Entertainment'':
                        sdiskusage(total=56955559936, used=15403667456, free=38635122688, percent=27.0)}
            uptime_formatted: dictionary of uptime split in days, hours, min, ex.
                    {'hours': '2 hours', 'days': '6 days', 'min': '26 minutes'}
        :return: dict
        """
        mem_info = psutil.virtual_memory()
        system_uptime = get_system_uptime()
        load_avg = os.getloadavg()
        return dict(mem_total=convert_bytes(mem_info[0], 'MB'),
                    mem_available=convert_bytes(mem_info[1], 'MB'),
                    mem_used_pct=mem_info[2],
                    mem_bars=self._memory_bars(mem_info[2]),
                    load_avg=load_avg,
                    uptime_formatted=system_uptime['uptime_formatted'])

    @staticmethod
    def _memory_bars(val_pct):
        mid = 50
        upper = 80
        ret = dict(xmin=min(val_pct, mid),
                   xmid=min(val_pct - mid, upper - mid),
                   xmax=min(val_pct - upper, 100 - upper))
        return {k: max(ret[k], 0) for k in ret}


if __name__ == '__main__':
    pass