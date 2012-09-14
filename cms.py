#!/usr/bin/env python

from copy import copy
import csv
import os

import boto
from boto.s3.key import Key
from flask import Flask
from flask import render_template, request
import pusher

import cms_settings as settings

app = Flask(__name__)

def push_to_s3():
    conn = boto.connect_s3()
    bucket = conn.get_bucket(settings.S3_BUCKET)
    key = Key(bucket)
    key.key = settings.S3_KEY
    key.set_contents_from_filename(settings.STATES_FILENAME)
    key.set_acl('public-read')

def push_live(event, data):
    pusher.app_id = settings.PUSHER_APP_ID
    pusher.key = os.environ['PUSHER_KEY']
    pusher.secret = os.environ['PUSHER_SECRET']

    p = pusher.Pusher()

    p[settings.PUSHER_CHANNEL].trigger(event, data)

@app.route('/', methods=['GET', 'POST'])
def login():
    with open(settings.STATES_FILENAME, 'r') as f:
        reader = csv.DictReader(f)
        
        states = [row for row in reader]

    if request.method == 'POST':
        new_states = []
        changes = {
            'likely': [],
            'called': [],
            'actual': []
        }

        for state in states:
            new_state = copy(state)
            new_state['likely'] = request.form['likely-%s' % state['id']]
            new_state['called'] = request.form['called-%s' % state['id']]
            new_state['actual'] = request.form['actual-%s' % state['id']]
            new_states.append(new_state)

            for edit_type in settings.RESULT_TYPES:
                if state[edit_type] != new_state[edit_type]:
                    changes[edit_type].append(new_state)

        with open(settings.STATES_FILENAME, 'w') as f:
            writer = csv.DictWriter(f, settings.STATES_HEADER)
            writer.writeheader()
            writer.writerows(new_states)

        push_to_s3()

        for edit_type in settings.RESULT_TYPES:
            if changes[edit_type]:
                #push_live('%s-change' % edit_type, changes[edit_type])
                pass

        states = new_states

    context = {
        'states': states, 
        'LIKELY_OPTIONS': settings.LIKELY_OPTIONS,
        'RESULT_TYPES': settings.RESULT_TYPES,
        'RESULT_OPTIONS': settings.RESULT_OPTIONS,
        'STATIC_URL': settings.STATIC_URL
    }

    return render_template('winners.html', **context)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=settings.DEBUG)

