#!/usr/bin/env python

import datetime
import os

# Project settings.
DATABASE_NAME = 'electris'
DATABASE_USER = 'electris'
DATABASE_PASSWORD = 'electris'
POLLING_INTERVAL = 15

# Constants for Electris the Web app.
PRESIDENT_HEADER = ['id', 'stateface', 'name', 'abbr', 'electoral_votes', 'polls_close', 'prediction', 'call', 'called_at', 'called_by', 'total_precincts', 'precincts_reporting', 'rep_vote_count', 'dem_vote_count']
PREDICTION_OPTIONS = [('sd', 'Solid Democrat'), ('ld', 'Leaning Democrat'), ('t', 'Tossup'), ('lr', 'Leaning Republican'), ('sr', 'Solid Republican')]
RESULT_OPTIONS = [('d', 'Democrat'), ('u', 'Undecided'), ('r', 'Republican')]

# Poll closing times.
CLOSING_TIMES = [
    datetime.datetime(2012, 11, 7, 0, 0),
    datetime.datetime(2012, 11, 7, 0, 30,),
    datetime.datetime(2012, 11, 7, 1, 0),
    datetime.datetime(2012, 11, 7, 1, 30),
    datetime.datetime(2012, 11, 7, 2, 0),
    datetime.datetime(2012, 11, 7, 3, 0),
    datetime.datetime(2012, 11, 7, 4, 0),
    datetime.datetime(2012, 11, 7, 5, 0)
]

# Constants for static media storage.
if os.environ.get('DEPLOYMENT_TARGET', '') == 'production':
    S3_BUCKET = 'election2012.npr.org'
    DEBUG = False
else:
    S3_BUCKET = 'stage-election2012.npr.org.s3.amazonaws.com'
    DEBUG = True
PRESIDENT_S3_KEY = 'states.csv'
PRESIDENT_FILENAME = 'www/states.json'

HOUSE_S3_KEY = 'house.json'
HOUSE_FILENAME = 'www/house.json'

SENATE_S3_KEY = 'senate.json'
SENATE_FILENAME = 'www/senate.json'

PRESIDENT_JSON_S3_KEY = 'president.json'
PRESIDENT_JSON_FILENAME = 'www/president.json'

# This is a change for Jeremy.
# For some reason, the stage-apps version of the bootstrap stuff went missing Monday night.
# So I'm using my local versions if there's an environment variable called LOCAL_DEV which is true.
if os.environ.get('LOCAL_DEV', '') == 'true':
    STATIC_URL = 'http://127.0.0.1:8000'
else:
    STATIC_URL = 'http://%s' % (S3_BUCKET)
