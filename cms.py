#!/usr/bin/env python

from datetime import datetime
import json
from sets import Set

from flask import Flask
from flask import render_template, request
import pytz

import cms_settings as settings
from util import (
    get_database, get_states, regenerate_csv, push_results_to_s3, get_house_candidates, get_senate_candidates)
from fetch_ap_results import CANDIDATE_MODEL_FIELDS

app = Flask(__name__)

@app.route('/', methods=['GET'])
def race_list():
    """
    Return a list of races in case someone gets to the main page.
    """

    return """
        <html>
            <body>
                <h1>Admin: Races</h1>
                <a href='/president/'>Presidential</a><br/>
                <a href='/house/'>U.S. House</a><br/>
                <a href='/senate'>U.S. Senate</a>
            </body>
        </html>
    """

@app.route('/house/', methods=['GET'])
def house_candidates():
    """
    Read/update list of results-by-district for the U.S. House election.
    This is limited to the "state_candidates" table in the SQLite DB.
    """
    db = get_database()
    candidates = get_house_candidates(db)
    db.close()

    context = {
        'settings': settings,
        'candidates': candidates,
        'race': 'U.S. House'
    }

    return render_template('house_senate_cms.html', **context)

@app.route('/senate/', methods=['GET'])
def senate_candidates():
    """
    Read/update list of results-by-state for the U.S. Senate election.
    This is limited to the "state_candidates" table in the SQLite DB.
    """
    db = get_database()
    candidates = get_senate_candidates(db)
    db.close()

    context = {
        'settings': settings,
        'candidates': candidates,
        'race': 'U.S. Senate'
    }

    return render_template('house_senate_cms.html', **context)

@app.route('/president/', methods=['GET', 'POST'])
def presidential_results():
    """
    Read/update list of results-by-state for the Presidential election.
    This is limited to the "states" table in the SQLite DB.
    """
    db = get_database()
    states = get_states(db)

    if request.method == 'POST':
        for state in states:
            prediction = request.form.get('prediction-%s' % state['id'], '')
            accept_ap_call = 'y' if request.form.get('accept-ap-call-%s' % state['id'], '') == 'on' else 'n'
            npr_call = request.form.get('npr-%s' % state['id'], '')
            npr_called_at = state['npr_called_at']

            # If NPR call updated, save time of change
            if npr_call != state['npr_call']:
                npr_called_at = datetime.now(tz=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S %z');

            db.execute('UPDATE states SET prediction=?, accept_ap_call=?, npr_call=?, npr_called_at=? WHERE id=?', (prediction, accept_ap_call, npr_call, npr_called_at, state['id']))

        db.commit()

        states = get_states(db)

        # When deployed, the CMS does not update the data files to prevent bad interactions with the AP cron job.
        if settings.DEBUG:
            regenerate_csv(states)
            push_results_to_s3()

    db.close()

    context = {
        'settings': settings,
        'states': states,
        'race': 'Presidential'
    }

    return render_template('president_cms.html', **context)

@app.route('/president/data/', methods=['GET', 'POST'])
def data():
    db = get_database()
    states = get_states(db)

    return json.dumps([dict(zip(s.keys(), s)) for s in states])

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=settings.DEBUG)

