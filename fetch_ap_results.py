#!/usr/bin/env python

from cStringIO import StringIO
from datetime import datetime
from ftplib import FTP
import os

import pytz

import cms_settings as settings
from util import (
    get_database, get_house_senate, regenerate_president, write_house_json, write_senate_json,
    get_states, push_results_to_s3)

OUTPUT_FIELDS = ['id', 'total_precincts', 'precincts_reporting', 'rep_vote_count', 'dem_vote_count', 'winner']


def parse_president(db, row):
    state_data = dict(zip(settings.STATE_FIELDS, row[:settings.NUM_STATE_FIELDS]))
    candidate_count = (len(row) - settings.NUM_STATE_FIELDS) / settings.NUM_CANDIDATE_FIELDS

    i = 0
    obama_data = None
    romney_data = None

    while i < candidate_count:
        first_field = settings.NUM_STATE_FIELDS + (i * settings.NUM_CANDIDATE_FIELDS)
        last_field = first_field + settings.NUM_CANDIDATE_FIELDS
        candidate_data = dict(zip(settings.CANDIDATE_FIELDS, row[first_field:last_field]))

        if candidate_data['last_name'] == 'Obama':
            obama_data = candidate_data
        elif candidate_data['last_name'] == 'Romney':
            romney_data = candidate_data

        if obama_data and romney_data:
            break

        i += 1

    assert obama_data and romney_data

    state_id = state_data['state_postal'].lower()

    old_state = db.execute('SELECT * FROM states WHERE id=?', (state_id,)).next()

    ap_call = 'r' if romney_data['is_winner'] else 'd' if obama_data['is_winner'] else 'u'
    ap_called_at = old_state['ap_called_at']

    if ap_call != old_state['ap_call']:
        ap_called_at = datetime.now(tz=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S %z')

    db.execute('UPDATE states SET ap_call=?, ap_called_at=?, total_precincts=?, precincts_reporting=?, rep_vote_count=?, dem_vote_count=? WHERE id=?', (ap_call, ap_called_at, state_data['total_precincts'], state_data['precincts_reporting'], romney_data['vote_count'], obama_data['vote_count'], state_id))


def parse_state_race(db, row):
    state_data = dict(zip(settings.STATE_FIELDS, row[:settings.NUM_STATE_FIELDS]))

    candidate_count = (len(row) - settings.NUM_STATE_FIELDS) / settings.NUM_CANDIDATE_FIELDS

    i = 0

    while i < candidate_count:
        first_field = settings.NUM_STATE_FIELDS + (i * settings.NUM_CANDIDATE_FIELDS)
        last_field = first_field + settings.NUM_CANDIDATE_FIELDS

        candidate_data = dict(zip(settings.CANDIDATE_FIELDS, row[first_field:last_field]))

        db.execute(
            'UPDATE house_senate_candidates SET\
                precincts_reporting=?,\
                total_precincts=?,\
                vote_count=?,\
                ap_winner=? \
                WHERE ap_npid=?',
                (
                    state_data['precincts_reporting'],
                    state_data['total_precincts'],
                    candidate_data['vote_count'],
                    candidate_data['is_winner'],
                    candidate_data['national_politician_id']
                )
            )

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
            pass
        elif race == 'U.S. House':
            parse_state_race(db, row_data)
        elif race == 'U.S. Senate':
            parse_state_race(db, row_data)

    db.commit()

    regenerate_president(get_states(db))
    write_house_json(get_house_senate(db))
    write_senate_json(get_house_senate(db))
    push_results_to_s3()

if __name__ == "__main__":
    main()
