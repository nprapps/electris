#!/usr/bin/env python

import csv
import sqlite3 as sqlite

from cms_settings import DATABASE_FILENAME

def get_database():
    """
    Fetch the sqlite DB being used for state data.
    """
    db = sqlite.connect(DATABASE_FILENAME)
    db.row_factory = sqlite.Row

    if not db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='states'").fetchone():
        bootstrap_database(db)

    return db

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

