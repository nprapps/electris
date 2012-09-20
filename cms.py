#!/usr/bin/env python

import csv

from flask import Flask
from flask import render_template, request

import cms_settings as settings
from push_results_to_s3 import push_results_to_s3
from util import get_database, get_states

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
            new_prediction = request.form.get('prediction-%s' % state['id'], '')
            new_npr_call = request.form.get('npr-%s' % state['id'], '')

            db.execute('UPDATE states SET prediction=?, npr_call=? WHERE id=?', (new_prediction, new_npr_call, state['id']))

        db.commit()
        
        states = get_states(db)

        with open(settings.STATES_FILENAME, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(settings.STATES_HEADER)

            for state in states:
                writer.writerow([f for f in state])

        push_results_to_s3()

    db.close()

    context = {
        'states': states, 
        'PREDICTION_OPTIONS': settings.PREDICTION_OPTIONS,
        'RESULT_OPTIONS': settings.RESULT_OPTIONS,
        'STATIC_URL': settings.STATIC_URL
    }

    return render_template('winners.html', **context)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=settings.DEBUG)

