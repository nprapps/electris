#!/usr/bin/env python

from pollster import Pollster

STATES = ['al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'dc', 'fl', 'ga', 'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md', 'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj', 'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc', 'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy']

pollster = Pollster()

for state in STATES:
    charts = pollster.charts(topic='2012-president', state=state)

    if charts:
        chart = charts[0]
    else:
        print 'NO DATA FOR %s' % state
        continue

    obama = 0
    romney = 0

    if chart.estimates:
        for estimate in chart.estimates:
            if estimate['choice'] == "Obama":
                obama = estimate['value']
            elif estimate['choice'] == "Romney":
                romney = estimate['value']
    else:
        print 'NO ESTIMATES FOR %s' % state
        continue

    #print "%s: %.2f to %.2f" % (state, obama, romney)
