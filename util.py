#!/usr/bin/env python

import csv
import json
import sqlite3 as sqlite
from cStringIO import StringIO
from ftplib import FTP
import os

import boto
from boto.s3.key import Key

import cms_settings as settings


def get_database():
    """
    Fetch the sqlite DB being used for state data.
    Actually calls bootstrap_database() if there aren't tables.
    Aha!
    Note: Only works for presidential ATM.
    """
    db = sqlite.connect(settings.DATABASE_FILENAME)
    db.row_factory = sqlite.Row

    if not db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='states'").fetchone():
        bootstrap_database(db)

    return db


def preload_state_race(db, row):
    state_data = dict(zip(settings.STATE_FIELDS, row[:settings.NUM_STATE_FIELDS]))

    candidate_count = (len(row) - settings.NUM_STATE_FIELDS) / settings.NUM_CANDIDATE_FIELDS

    i = 0

    while i < candidate_count:
        first_field = settings.NUM_STATE_FIELDS + (i * settings.NUM_CANDIDATE_FIELDS)
        last_field = first_field + settings.NUM_CANDIDATE_FIELDS

        candidate_data = dict(zip(settings.CANDIDATE_FIELDS, row[first_field:last_field]))
        party = 'Other'
        is_winner = '0'
        if candidate_data['party'] in ['Dem', 'GOP']:
            party = candidate_data['party']
        if candidate_data['is_winner'] != '':
            is_winner = '1'
        db.execute(
            'INSERT INTO house_senate_candidates VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (
                    state_data['state_postal'],
                    state_data['county_name'],
                    state_data['office_id'],
                    state_data['seat_number'],
                    state_data['office_name'],
                    state_data['seat_name'],
                    state_data['precincts_reporting'],
                    state_data['total_precincts'],
                    candidate_data['national_politician_id'],
                    candidate_data['first_name'],
                    candidate_data['last_name'],
                    candidate_data['middle_name'],
                    candidate_data['junior'],
                    candidate_data['use_junior'],
                    candidate_data['incumbent'],
                    party,
                    candidate_data['vote_count'],
                    is_winner,
                    "",
                    "0",
                    "",
                    "1",
                    '%s %s' % (
                        state_data['state_postal'].lower(),
                        state_data['seat_number'])
                )
            )

        i += 1


def bootstrap_database(db):
    """
    Create the sqlite DB and a populate it with data.
    Note: Only works for presidential ATM.
    """
    db.execute('CREATE TABLE states (id text, stateface text, name text, abbr text, electoral_votes integer, polls_close text, prediction text, ap_call text, ap_called_at text, accept_ap_call text, npr_call text, npr_called_at text, total_precincts integer, precincts_reporting integer, rep_vote_count integer, dem_vote_count integer)')

    with open('states_bootstrap.csv') as f:
        reader = csv.reader(f)
        reader.next()

        db.executemany('INSERT INTO states VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', reader)

    db.execute('CREATE TABLE house_senate_candidates (\
        state_postal text,\
        state_name text,\
        office_code text,\
        district_id integer,\
        office_name text,\
        district_name text,\
        precincts_reporting integer,\
        total_precincts integer,\
        ap_npid text,\
        first_name text,\
        last_name text,\
        middle_name text,\
        junior text,\
        use_junior text,\
        incumbent text,\
        party text,\
        vote_count text,\
        ap_winner text,\
        ap_winner_time text,\
        npr_winner text,\
        npr_winner_time text,\
        accept_ap_call text,\
        race_slug)')

    data = StringIO()

    ftp = FTP('electionsonline.ap.org')
    ftp.login(os.environ['AP_USERNAME'], os.environ['AP_PASSWORD'])
    ftp.retrbinary('RETR US_topofticket/flat/US.txt', data.write)
    ftp.quit()

    # Rebuffer data
    data = StringIO(data.getvalue())

    for row in data:
        row_data = row.split(';')

        race = row_data[10]

        if race == 'U.S. House':
            preload_state_race(db, row_data)
        elif race == 'U.S. Senate':
            preload_state_race(db, row_data)

    db.commit()


def get_states(db):
    """
    Fetch states from sqlite as a list.
    """
    return db.execute('SELECT * FROM states').fetchall()


def get_house_senate(db):
    """
    Fetch candidates for house/senate from sqlite as a list.
    """
    return db.execute('SELECT * FROM house_senate_candidates').fetchall()


def write_president_json(states):
    with open('www/president.json', 'w') as f:
        times = settings.PRESIDENT_TIMES
        objects = []
        for timezone in times:
            timezone_dict = {}
            timezone_dict['gmt_epoch_time'] = timezone['time']
            timezone_dict['states'] = []
            for s in timezone['states']:
                for state in states:
                    if state['id'].upper() == s:
                        timezone_dict['states'].append(dict(state))
            objects.append(timezone_dict)
        f.write(json.dumps(objects))


def write_house_json(candidates):
    with open(settings.HOUSE_FILENAME, 'w') as f:
        f.write(generate_json(candidates, (u'house', u'H')))


def write_senate_json(candidates):
    with open(settings.SENATE_FILENAME, 'w') as f:
        f.write(generate_json(candidates, (u'senate', u'S')))


def generate_json(rows, house):
    """
    Generates JSON from rows of candidates and a house of congress.
    * Rows should be an iterator. In this case, a query for a set of candidates.
    * House should be a two-tuple: ('house', 'h').
    * Results should be an integer. 0 means return all.
    """
    times = getattr(settings, '%s_TIMES' % house[0].upper())
    objects = []
    for timezone in times:
        timezone_dict = {}
        timezone_dict['gmt_epoch_time'] = timezone['time']
        timezone_dict['districts'] = []
        for district in timezone['districts']:
            district_dict = {}
            district_dict['district'] = district
            district_dict['candidates'] = []
            district_dict['district_slug'] = district.replace(' ', '').lower()
            district_dict['called'] = False
            district_dict['called_time'] = None
            for candidate in rows:
                if candidate[0] == district.split(' ')[0]:
                    if int(candidate[3]) == int(district.split(' ')[1]):
                        if (
                            candidate[15] == u'Dem'
                            or candidate[15] == u'GOP'
                            or candidate[9] == 'Angus'):
                            if candidate[2] == house[1]:
                                candidate_dict = dict(zip(
                                            settings.HOUSE_SENATE_HEADER,
                                            candidate))

                                candidate_dict['winner'] = False

                                if candidate_dict['accept_ap_call'] == "1":
                                    if candidate_dict['ap_winner'] == "1":
                                        district_dict['called'] = True
                                        candidate_dict['winner'] = True
                                else:
                                    if candidate_dict['npr_winner'] == "1":
                                        district_dict['called'] = True
                                        candidate_dict['winner'] = True

                                ### THIS NEEDS TO DO SOMETHING WITH TIME EVENTUALLY ###
                                district_dict['called_time'] = None

                                if candidate[10] != 'Dill':
                                    district_dict['candidates'].append(candidate_dict)
            district_dict['candidates'] = sorted(
                district_dict['candidates'],
                key=lambda candidate: candidate['party'])
            timezone_dict['districts'].append(district_dict)
        objects.append(timezone_dict)
    return json.dumps(objects)


def regenerate_president(states):
    """
    Rewrites CSV files from the DB for president.
    """
    with open(settings.PRESIDENT_FILENAME, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(settings.PRESIDENT_HEADER)

        for state in states:
            state = dict(state)

            if state['npr_call'] != 'n' and state['npr_call'] != 'u':
                state['call'] = state['npr_call']
                state['called_at'] = state['npr_called_at']
                state['called_by'] = 'npr'
            elif state['accept_ap_call'] == 'y' and state['ap_call'] != 'u':
                state['call'] = state['ap_call']
                state['called_at'] = state['ap_called_at']
                state['called_by'] = 'ap'
            else:
                state['call'] = None
                state['called_at'] = None
                state['called_by'] = None

            writer.writerow([state[f] for f in settings.PRESIDENT_HEADER])


def push_results_to_s3():
    """
    Push president and house/senate CSV files to S3.
    """
    # Some mildly global settings.
    conn = boto.connect_s3()
    bucket = conn.get_bucket(settings.S3_BUCKET)
    headers = {'Cache-Control': 'max-age=0 no-cache no-store must-revalidate'}
    policy = 'public-read'

    # Push the president csv file.
    if os.path.exists(settings.PRESIDENT_FILENAME):
        president_key = Key(bucket)
        president_key.key = settings.PRESIDENT_S3_KEY
        president_key.set_contents_from_filename(
            settings.PRESIDENT_FILENAME,
            policy=policy,
            headers=headers)

    # Push the house csv file.
    if os.path.exists(settings.HOUSE_FILENAME):
        house_key = Key(bucket)
        house_key.key = settings.HOUSE_S3_KEY
        house_key.set_contents_from_filename(
            settings.HOUSE_FILENAME,
            policy=policy,
            headers=headers)

    # Push the senate csv file.
    if os.path.exists(settings.SENATE_FILENAME):
        senate = Key(bucket)
        senate.key = settings.SENATE_S3_KEY
        senate.set_contents_from_filename(
            settings.SENATE_FILENAME,
            policy=policy,
            headers=headers)
