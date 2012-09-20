#!/usr/bin/env python

from cStringIO import StringIO
from ftplib import FTP
import os

from util import get_database, get_states, regenerate_csv, push_results_to_s3

STATES = ['al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'dc', 'fl', 'ga', 'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md', 'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj', 'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc', 'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy']

STATE_FIELDS = [
    'is_test',
    'election_date',
    'state_postal',
    'county_number',
    'fips',
    'county_name',
    'race_number',
    'office_id',
    'race_type_id',
    'seat_number',
    'office_name',
    'seat_name',
    'race_type_party',
    'race_type',
    'office_description',
    'number_of_winners',
    'number_in_runoff',
    'precincts_reporting',
    'total_precincts'
]

CANDIDATE_FIELDS = [
    'candidate_number',
    'order',
    'party',
    'first_name',
    'middle_name',
    'last_name',
    'junior',
    'use_junior',
    'incumbent',
    'vote_count',
    'is_winner',
    'national_politician_id',
]

NUM_STATE_FIELDS = len(STATE_FIELDS)
NUM_CANDIDATE_FIELDS = len(CANDIDATE_FIELDS)

OUTPUT_FIELDS = ['id', 'total_precincts', 'precincts_reporting', 'rep_vote_count', 'dem_vote_count', 'winner']

data = StringIO()

ftp = FTP('electionsonline.ap.org')
ftp.login(os.environ['AP_USERNAME'], os.environ['AP_PASSWORD'])
ftp.retrbinary('RETR US_topofticket/flat/US.txt', data.write)
ftp.quit()

# Rebuffer data
data = StringIO(data.getvalue())

db = get_database()

for row in data:
    row_data = row.split(';')

    state_data = dict(zip(STATE_FIELDS, row_data[:NUM_STATE_FIELDS]))

    if state_data['office_name'] != 'President':
        continue

    candidate_count = (len(row_data) - NUM_STATE_FIELDS) / NUM_CANDIDATE_FIELDS 

    i = 0
    obama_data = None
    romney_data = None

    while i < candidate_count:
        first_field = NUM_STATE_FIELDS + (i * NUM_CANDIDATE_FIELDS)
        last_field = first_field + NUM_CANDIDATE_FIELDS
        candidate_data = dict(zip(CANDIDATE_FIELDS, row_data[first_field:last_field]))

        if candidate_data['last_name'] == 'Obama':
            obama_data = candidate_data
        elif candidate_data['last_name'] == 'Romney':
            romney_data = candidate_data

        if obama_data and romney_data:
            break

        i += 1

    assert obama_data and romney_data

    state = state_data['state_postal'].lower()
    winner = 'r' if romney_data['is_winner'] else 'd' if obama_data['is_winner'] else ''

    db.execute('UPDATE states SET ap_call=?, total_precincts=?, precincts_reporting=?, rep_vote_count=?, dem_vote_count=? WHERE id=?', (winner, state_data['total_precincts'], state_data['precincts_reporting'], romney_data['vote_count'], obama_data['vote_count'], state)) 

db.commit()

regenerate_csv(get_states(db))
push_results_to_s3()

