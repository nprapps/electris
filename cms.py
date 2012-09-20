#!/usr/bin/env python

import csv
import sqlite3 as sqlite

import boto
from boto.s3.key import Key
from flask import Flask
from flask import render_template, request

import cms_settings as settings

app = Flask(__name__)

def bootstrap_database(db):
    """
    Create the sqlite DB and a populate it with data.
    """
    db.execute('CREATE TABLE states (id text, stateface text, name text, electoral_votes integer, prediction text, ap_call text, npr_call text, total_precincts, precincts_reporting, rep_vote_count, dem_vote_count)') 

    with open('states_bootstrap.csv') as f:
        reader = csv.reader(f)
        reader.next()

        db.executemany('INSERT INTO states VALUES(?,?,?,?,?,?,?,?,?,?,?)', reader)

    db.commit()

def get_states(db):
    """
    Fetch states from sqlite as a list.
    """
    return db.execute('SELECT * FROM states').fetchall()

def push_to_s3():
    """
    Push current states CSV file to S3.
    """
    conn = boto.connect_s3()
    bucket = conn.get_bucket(settings.S3_BUCKET)
    key = Key(bucket)
    key.key = settings.S3_KEY
    key.set_contents_from_filename(
        settings.STATES_FILENAME,
        policy='public-read',
        headers={'Cache-Control': 'max-age=0 no-cache no-store must-revalidate'}
    )

@app.route('/', methods=['GET', 'POST'])
def winners():
    """
    Read/update list of state winners.
    """
    db = sqlite.connect('electris.db')
    db.row_factory = sqlite.Row

    if not db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='states'").fetchone():
        bootstrap_database(db)

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

        push_to_s3()

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

