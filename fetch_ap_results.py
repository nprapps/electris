#!/usr/bin/env python

from cStringIO import StringIO
from ftplib import FTP
import os

from util import get_database, get_states, regenerate_csv, push_results_to_s3

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

def parse_president(db, row):
    state_data = dict(zip(STATE_FIELDS, row[:NUM_STATE_FIELDS]))

    candidate_count = (len(row) - NUM_STATE_FIELDS) / NUM_CANDIDATE_FIELDS 

    i = 0
    obama_data = None
    romney_data = None

    while i < candidate_count:
        first_field = NUM_STATE_FIELDS + (i * NUM_CANDIDATE_FIELDS)
        last_field = first_field + NUM_CANDIDATE_FIELDS
        candidate_data = dict(zip(CANDIDATE_FIELDS, row[first_field:last_field]))

        if candidate_data['last_name'] == 'Obama':
            obama_data = candidate_data
        elif candidate_data['last_name'] == 'Romney':
            romney_data = candidate_data

        if obama_data and romney_data:
            break

        i += 1

    assert obama_data and romney_data

    state = state_data['state_postal'].lower()
    winner = 'r' if romney_data['is_winner'] else 'd' if obama_data['is_winner'] else 'u'

    db.execute('UPDATE states SET ap_call=?, total_precincts=?, precincts_reporting=?, rep_vote_count=?, dem_vote_count=? WHERE id=?', (winner, state_data['total_precincts'], state_data['precincts_reporting'], romney_data['vote_count'], obama_data['vote_count'], state)) 

def parse_state_race(db, row):
    state_data = dict(zip(STATE_FIELDS, row[:NUM_STATE_FIELDS]))

    candidate_count = (len(row) - NUM_STATE_FIELDS) / NUM_CANDIDATE_FIELDS 

    i = 0
    
    state = state_data['state_postal'].lower()

    while i < candidate_count:
        first_field = NUM_STATE_FIELDS + (i * NUM_CANDIDATE_FIELDS)
        last_field = first_field + NUM_CANDIDATE_FIELDS

        candidate_data = dict(zip(CANDIDATE_FIELDS, row[first_field:last_field]))
        
        db.execute('DELETE FROM state_candidates WHERE state_id=? AND ballot_order=?', (state, candidate_data['order']))
        db.execute('INSERT INTO state_candidates VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (state, state_data['office_name'], candidate_data['order'], candidate_data['party'], candidate_data['first_name'], candidate_data['middle_name'], candidate_data['last_name'], candidate_data['junior'], candidate_data['use_junior'], candidate_data['incumbent'], candidate_data['vote_count'], candidate_data['is_winner'])) 

        i += 1

def main():
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

        race = row_data[10]

        if race == 'President':
            parse_president(db, row_data)
        elif race == 'U.S. House':
            parse_state_race(db, row_data) 
        elif race == 'U.S. Senate':
            parse_state_race(db, row_data) 

    db.commit()

    regenerate_csv(get_states(db))
    push_results_to_s3()

if __name__ == "__main__":
    main()

