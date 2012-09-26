#!/usr/bin/env python

import csv
import sqlite3 as sqlite

import boto
from boto.s3.key import Key

import cms_settings as settings 

def get_database():
    """
    Fetch the sqlite DB being used for state data.
    """
    db = sqlite.connect(settings.DATABASE_FILENAME)
    db.row_factory = sqlite.Row

    if not db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='states'").fetchone():
        bootstrap_database(db)

    return db

def bootstrap_database(db):
    """
    Create the sqlite DB and a populate it with data.
    """
    db.execute('CREATE TABLE states (id text, stateface text, name text, electoral_votes integer, prediction text, ap_call text, accept_ap_call text, npr_call text, total_precincts integer, precincts_reporting integer, rep_vote_count integer, dem_vote_count integer)') 

    with open('states_bootstrap.csv') as f:
        reader = csv.reader(f)
        reader.next()

        db.executemany('INSERT INTO states VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', reader)

    db.execute('CREATE TABLE state_candidates (state_id text, race text, ballot_order integer, party text, first_name text, middle_name text, last_name text, junior text, use_junior text, incumbent text, vote_count integer, is_winner text)') 

    db.commit()

def get_states(db):
    """
    Fetch states from sqlite as a list.
    """
    return db.execute('SELECT * FROM states').fetchall()

def regenerate_csv(states):
    """
    Regenerate the states CSV from DB states.
    """
    with open(settings.STATES_FILENAME, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(settings.STATES_HEADER)

        for state in states:
            writer.writerow([f for f in state])

def push_results_to_s3():
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

