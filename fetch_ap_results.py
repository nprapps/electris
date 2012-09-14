#!/usr/bin/env python

import json
import os

from elections import AP

STATES = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

output = {}

client = AP(os.environ['AP_USERNAME'], os.environ['AP_PASSWORD'])
print client.get_topofticket('2012-11-06')

for state in STATES:
    print 'Fetching %s' % state
    ap_state = client.get_state('IA')

    ap_races = ap_state.filter_races(office_name='President')

    assert len(ap_races) == 1

    ap_race = ap_races[0]

    result = {}
    
    for ap_result in ap_race.state.results:
        if ap_result.candidate.last_name not in ['Obama', 'Romney']:
            continue

        result[ap_result.candidate.last_name] = {
            'vote_total': ap_result.vote_total,
            'vote_total_percent': ap_result.vote_total_percent
        }

    output[state] = result

with open('results.js', 'w') as f:
    f.write(json.dumps(output))

