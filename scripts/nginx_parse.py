#!/usr/bin/env python

# Pipe any nginx log file(s) to this script and monthly counts will
# be output to stdout chronologically in the format:
#
#    (YYYY, MM) IP HITS
#
# On stderr, monthly totals will be output after each month. At the
# end, global stats will be printed.

from sys import stderr
from fileinput import input
from re import compile
from datetime import datetime
from collections import defaultdict

# https://coderwall.com/p/snn1ag/regex-to-parse-your-default-nginx-access-logs

pattern = ""
pattern += '(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - '
pattern += '\[(?P<dateandtime>\d{2}\/[a-zA-Z]{3}\/'
pattern += '\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] '
pattern += '(.*?)'
# pattern += '((\"(GET|POST) )(?P<url>.+)(http\/1\.1")) (?P<statuscode>\d{3}) '
# pattern += '(?P<bytessent>\d+) (["](?P<refferer>(\-)|(.+))["]) (["]'
# pattern += '(?P<useragent>.+)["])'
pattern = compile(pattern)


def dt_parse(t):
    # TODO: needs timedelta returned
    return datetime.strptime(t[0:20], '%d/%b/%Y:%H:%M:%S')


def print_month(month, per_month):
    if not per_month:
        return
    ips, hits = tuple(per_month)
    if ips or hits:
        msg = "%s Month totals: IPs=%s Hits=%s" % (month, len(ips), hits)
        print >>stderr, msg


data = defaultdict(lambda: defaultdict(int))
for line in input():
    line = line.strip()
    m = pattern.match(line)
    if not m:
        print "skipping", line
        continue
    g = m.groups()
    d = dt_parse(g[1])
    t = d.timetuple()
    # t = mktime(d.timetuple())
    data[(t[0], t[1])][g[0]] += 1

total_hits = 0
total_ips = set()
cur_month = None
per_month = None
for k, v in sorted(data.items()):
    if k != cur_month:
        print_month(k, per_month)
        per_month = [set(), 0]
    for ip, count in sorted(v.items()):
        total_hits += count
        total_ips.add(ip)
        per_month[1] += count
        per_month[0].add(ip)
        print k, ip, count
print_month(k, per_month)  # Leftovers
print >>stderr, "Total hits:", total_hits
print >>stderr, "Unique IPs:", len(total_ips)
