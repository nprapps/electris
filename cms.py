#!/usr/bin/env python

import json

from flask import Flask
from flask import render_template, request

import cms_settings as settings
from util import get_database, get_states, regenerate_csv, push_results_to_s3

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def winners():
    """
    Read/update list of state winners.
    """
    db = get_database()
    states = get_states(db)
        
    if request.method == 'POST':
        for state in states:
            prediction = request.form.get('prediction-%s' % state['id'], '')
            accept_ap_call = 'y' if request.form.get('accept-ap-call-%s' % state['id'], '') == 'on' else 'n'
            npr_call = request.form.get('npr-%s' % state['id'], '')
            

            db.execute('UPDATE states SET prediction=?, accept_ap_call=?, npr_call=? WHERE id=?', (prediction, accept_ap_call, npr_call, state['id']))

        db.commit()

        states = get_states(db)

        # When deployed, the CMS does not update the data files to prevent bad interactions with the AP cron job.
        if settings.DEBUG:
            regenerate_csv(states)
            push_results_to_s3()

    db.close()

    context = {
        'states': states, 
        'PREDICTION_OPTIONS': settings.PREDICTION_OPTIONS,
        'RESULT_OPTIONS': settings.RESULT_OPTIONS,
        'STATIC_URL': settings.STATIC_URL
    }

    return render_template('winners.html', **context)

@app.route('/data', methods=['GET', 'POST'])
def data():
    db = get_database()
    states = get_states(db)

    return json.dumps([dict(zip(s.keys(), s)) for s in states])

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=settings.DEBUG)
