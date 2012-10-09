#!/usr/bin/env python

# Project settings.
PROJECT_NAME = 'electris'
DATABASE_FILENAME = 'electris.db'
POLLING_INTERVAL = 15

# Constants for Electris the Web app.
PRESIDENT_HEADER = ['id', 'stateface', 'name', 'abbr', 'electoral_votes', 'polls_close', 'prediction', 'call', 'called_at', 'called_by', 'total_precincts', 'precincts_reporting', 'rep_vote_count', 'dem_vote_count']
PREDICTION_OPTIONS = [('sd', 'Solid Democrat'), ('ld', 'Leaning Democrat'), ('t', 'Tossup'), ('lr', 'Leaning Republican'), ('sr', 'Solid Republican')]
RESULT_OPTIONS = [('d', 'Democrat'), ('u', 'Undecided'), ('r', 'Republican')]

# Constants for the BigBoard Web app.
HOUSE_SENATE_HEADER = [
    'state_postal',
    'state_name',
    'office_code',
    'district_id',
    'office_name',
    'district_name',
    'precincts_reporting',
    'total_precincts',
    'ap_npid',
    'first_name',
    'last_name',
    'middle_name',
    'junior',
    'use_junior',
    'incumbent',
    'party',
    'vote_count',
    'ap_winner',
    'ap_winner_time',
    'npr_winner',
    'npr_winner_time'
]

# Constants for static media storage.
import os
if os.environ.get('DEPLOYMENT_TARGET', '') == 'production':
    S3_BUCKET = 'apps.npr.org'
    DEBUG = False
else:
    S3_BUCKET = 'stage-apps.npr.org'
    DEBUG = True
PRESIDENT_S3_KEY = '%s/states.csv' % PROJECT_NAME
PRESIDENT_FILENAME = 'www/states.csv'
HOUSE_SENATE_S3_KEY = '%s/house_senate.csv' % PROJECT_NAME
HOUSE_SENATE_FILENAME = 'www/house_senate.csv'
STATIC_URL = 'http://%s/%s' % (S3_BUCKET, PROJECT_NAME)


# Constants for data imports.
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
