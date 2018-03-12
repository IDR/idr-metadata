#!/usr/bin/python

import json
from sys import argv

#
# Takes one micromanager rendering settings file (with name '*_mm_*.json') as argument and
# converts it to an OME compatible json file (with name '*_ome_*.json').
#

outchannels = []
outfile = ""

with open(argv[1], 'r') as f:
    outfile = argv[1].replace('_mm_', '_ome_')
    print('Converting micromanager rendering settings file \'%s\' to OME renderings settings file \'%s\'' % (argv[1], outfile))
    data = json.load(f)

    index = 1
    for channel in data['Channels']:
        outchannel = {}
        outchannel['index'] = index

        color = channel['Color']+2**24
        color = str(hex(color))
        color = color.replace('0x', '')
        outchannel['color'] = color

        if 'Name' in channel:
            outchannel['label'] = channel['Name']
        else:
            outchannel['label'] = "Channel %d" % index

        outchannel['min'] = channel['Min']

        outchannel['max'] = channel['Max']

        if 'DisplayMode' in channel and channel['DisplayMode'] == 1:
            outchannel['active'] = True
        else:
            outchannel['active'] = False

        outchannels.append(outchannel)

        index += 1

with open(outfile, 'w') as f:
    output = {}
    output['channels'] = outchannels
    f.write(json.dumps(output, indent=2))

