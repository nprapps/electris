#!/usr/bin/env python

import os

PROJECT_NAME = 'electris'

if os.environ.get('DEPLOYMENT_TARGET', '') == 'production':
    S3_BUCKET = 'apps.npr.org'
    DEBUG = False
else:
    S3_BUCKET = 'stage-apps.npr.org'
    DEBUG = True

DATABASE_FILENAME = 'electris.db'

S3_KEY = '%s/states.csv' % PROJECT_NAME

STATES_FILENAME = 'www/states.csv'
STATES_HEADER = ['id', 'stateface', 'name', 'abbr', 'electoral_votes', 'polls_close', 'prediction', 'ap_call', 'ap_called_at', 'accept_ap_call', 'npr_call', 'npr_called_at', 'total_precincts', 'precincts_reporting', 'rep_vote_count', 'dem_vote_count']

STATIC_URL = 'http://%s/%s' % (S3_BUCKET, PROJECT_NAME)

POLLING_INTERVAL = 15
PREDICTION_OPTIONS = [('sd', 'Solid Democrat'), ('ld', 'Leaning Democrat'), ('t', 'Tossup'), ('lr', 'Leaning Republican'), ('sr', 'Solid Republican')]
RESULT_OPTIONS = [('d', 'Democrat'), ('u', 'Undecided'), ('r', 'Republican')]

