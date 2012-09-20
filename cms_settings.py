#!/usr/bin/env python

import os

PROJECT_NAME = 'electris'

if os.environ.get('DEPLOYMENT_TARGET', '') == 'production':
    S3_BUCKET = 'apps.npr.org'
    DEBUG = False
else:
    S3_BUCKET = 'stage-apps.npr.org'
    DEBUG = True

S3_KEY = '%s/states.csv' % PROJECT_NAME

STATES_FILENAME = 'www/states.csv'
STATES_HEADER = ['id', 'stateface', 'name', 'electoral_votes', 'prediction', 'ap_call', 'npr_call', 'total_precincts', 'precincts_reporting', 'rep_vote_count', 'dem_vote_count']

STATIC_URL = 'http://%s/%s' % (S3_BUCKET, PROJECT_NAME)

PUSHER_APP_ID = '27515'
PUSHER_CHANNEL = 'elections-test'

PREDICTION_OPTIONS = [('sd', 'Solid Democrat'), ('ld', 'Leaning Democrat'), ('', 'Tossup'), ('lr', 'Leaning Republican'), ('sr', 'Solid Republican')]
RESULT_OPTIONS = [('d', 'Democrat'), ('', 'Undecided'), ('r', 'Republican')]

