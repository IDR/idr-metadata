#!/usr/bin/env python
# Print out a summary of existing tasks, and failure messages
# You will need a celeryconfig.py file in your current working directory
# Pass a list of task IDs to stdout, e.g.
#
#   ./get_failed.py < taskids.txt

import celery.result
import sys


st = {}
fail = {}
for line in sys.stdin:
    for taskid in line.split():
        r = celery.result.AsyncResult(taskid)
        try:
            st[r.status] += 1
        except KeyError:
            st[r.status] = 1
        if r.status == 'FAILURE':
            fail[taskid] = r

print('SUMMARY')
for k, v in st.items():
    print('  {}: {}'.format(k, v))
print('\nFAILURES')
for k, v in fail.items():
    print('  {}: {}'.format(k, v.info))
