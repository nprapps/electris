#!/usr/bin/env python

import os
import csv
import datetime
import pytz

import initial_data.time_zones as time_zones

from cStringIO import StringIO
from ftplib import FTP
from peewee import *
from pollster import Pollster

from models import Race, Candidate, State

RACE_FIELDS = [
    'is_test',
    'election_date',
    'state_postal',
    'county_number',
    'fips',
    'state_name',
    'race_number',
    'office_code',
    'race_type_id',
    'district_id',
    'office_name',
    'seat_name',
    'race_type_party',
    'race_type',
    'office_description',
    'number_of_winners',
    'number_in_runoff',
    'precincts_reporting',
    'total_precincts'
]

CANDIDATE_FIELDS = [
    'candidate_number',
    'ballot_order',
    'party',
    'first_name',
    'middle_name',
    'last_name',
    'junior',
    'use_junior',
    'incumbent',
    'vote_count',
    'ap_winner',
    'npid'
]

DISTRICT_RACE_FIELDS = [
    'is_test',
    'election_date',
    'state_postal',
    'district_type',
    'district_number',
    'district_name',
    'race_number',
    'office_code',
    'race_type_id',
    'seat_number',
    'office_name',
    'seat_name',
    'race_type_party',
    'race_type',
    'office_description',
    'number_of_winners',
    'number_in_runoff',
    'precincts_reporting',
    'total_precincts'
]

DISTRICT_CANDIDATE_FIELDS = [
    'candidate_number',
    'ballot_order',
    'party',
    'first_name',
    'middle_name',
    'last_name',
    'junior',
    'use_junior',
    'incumbent',
    'delegates',
    'vote_count',
    'ap_winner',
    'npid'
]


def get_fake_ap_data():
    """
    Grabs the selected fake AP top-of-ticket data file.
    """
    path = 'www/timemachine/US.txt'
    with open(path, 'rb') as f:
        return f.readlines()


def get_fake_ap_district_data(state_code):
    """
    Grabs the selected fake AP district data file.
    """
    path = 'www/timemachine/%s_D.txt' % state_code
    with open(path, 'rb') as f:
        return f.readlines()


def get_ap_data():
    data = StringIO()
    ftp = FTP('electionsonline.ap.org')
    ftp.login(os.environ['AP_USERNAME'], os.environ['AP_PASSWORD'])
    ftp.retrbinary('RETR US_topofticket/flat/US.txt', data.write)
    ftp.quit()
    data = StringIO(data.getvalue())
    return data


def get_ap_district_data(state_code):
    data = StringIO()
    ftp = FTP('electionsonline.ap.org')
    ftp.login(os.environ['AP_USERNAME'], os.environ['AP_PASSWORD'])
    ftp.retrbinary('RETR %s/flat/%s_D.txt' % (state_code, state_code), data.write)
    ftp.quit()
    data = StringIO(data.getvalue())
    return data


def parse_ap_data(data, ne_data, me_data):
    for i, row in enumerate(data):
        row_data = row.split(';')
        race = row_data[10]
        if race == 'President':
            parse_president(row_data)
        if race == 'U.S. House' or race == 'U.S. Senate':
            parse_house(row_data)

    for row in ne_data:
        row_data = row.split(';')
        race = row_data[10]

        if race == 'President':
            parse_president_district('NE', row_data)

    for row in me_data:
        row_data = row.split(';')
        race = row_data[10]

        if race == 'President':
            parse_president_district('ME', row_data)


def parse_house(row):
    race_data = dict(zip(RACE_FIELDS, row[:len(RACE_FIELDS)]))
    race_data['slug'] = u'%s%s' % (
        race_data['state_postal'].lower(), race_data['district_id'])
    candidate_count = (len(row) - len(RACE_FIELDS)) / len(CANDIDATE_FIELDS)

    rq = Race.update(
        precincts_reporting=race_data['precincts_reporting'],
    ).where(Race.slug == race_data['slug'])
    rq.execute()

    i = 0

    while i < candidate_count:
        first_field = len(RACE_FIELDS) + (i * len(CANDIDATE_FIELDS))
        last_field = first_field + len(CANDIDATE_FIELDS)

        candidate_data = dict(zip(CANDIDATE_FIELDS, row[first_field:last_field]))

        if candidate_data['ap_winner'] == 'X':
            candidate_data['ap_winner'] = True
        else:
            candidate_data['ap_winner'] = False

        if candidate_data['incumbent'] == "1":
            candidate_data['incumbent'] = True
        else:
            candidate_data['incumbent'] = False

        if candidate_data['ap_winner'] == True:
            rq = Race.update(
                ap_called=True,
                ap_called_time=datetime.datetime.now(tz=pytz.utc))\
            .where(Race.slug == race_data['slug'], Race.ap_called == False)
            rq.execute()

        cq = Candidate.update(
                ap_winner=candidate_data['ap_winner'],
                vote_count=candidate_data['vote_count']
            ).where(
            Candidate.npid == candidate_data['npid'])
        cq.execute()

        i += 1


def parse_president(row):
    race_data = dict(zip(RACE_FIELDS, row[:len(RACE_FIELDS)]))
    candidate_count = (len(row) - len(RACE_FIELDS)) / len(CANDIDATE_FIELDS)

    i = 0
    obama_data = None
    romney_data = None

    while i < candidate_count:
        first_field = len(RACE_FIELDS) + (i * len(CANDIDATE_FIELDS))
        last_field = first_field + len(CANDIDATE_FIELDS)

        candidate_data = dict(zip(CANDIDATE_FIELDS, row[first_field:last_field]))

        if candidate_data['last_name'] == 'Obama':
            obama_data = candidate_data
        elif candidate_data['last_name'] == 'Romney':
            romney_data = candidate_data

        if obama_data and romney_data:
            break

        i += 1

    assert obama_data and romney_data

    state = State.select().where(State.id == race_data['state_postal'].lower()).get()
    ap_call = 'r' if romney_data['ap_winner'] else 'd' if obama_data['ap_winner'] else 'u'

    ap_called_at = state.ap_called_at

    if ap_call != state.ap_call:
        ap_called_at = datetime.datetime.now(tz=pytz.utc)

    state.ap_call = ap_call
    state.ap_called_at = ap_called_at
    state.total_precincts = race_data['total_precincts']
    state.precincts_reporting = race_data['precincts_reporting']
    state.rep_vote_count = romney_data['vote_count']
    state.dem_vote_count = obama_data['vote_count']

    state.save()


def parse_president_district(state_code, row):
    race_data = dict(zip(DISTRICT_RACE_FIELDS, row[:len(DISTRICT_RACE_FIELDS)]))
    candidate_count = (len(row) - len(DISTRICT_RACE_FIELDS)) / len(DISTRICT_CANDIDATE_FIELDS)

    i = 0
    obama_data = None
    romney_data = None

    while i < candidate_count:
        first_field = len(DISTRICT_RACE_FIELDS) + (i * len(DISTRICT_CANDIDATE_FIELDS))
        last_field = first_field + len(DISTRICT_CANDIDATE_FIELDS)

        candidate_data = dict(zip(DISTRICT_CANDIDATE_FIELDS, row[first_field:last_field]))

        if candidate_data['last_name'] == 'Obama':
            obama_data = candidate_data
        elif candidate_data['last_name'] == 'Romney':
            romney_data = candidate_data

        if obama_data and romney_data:
            break

        i += 1

    assert obama_data and romney_data

    if race_data['district_name'] == state_code:
        q = (State.id == state_code.lower())
    else:
        district_number = race_data['district_name'][-1:]
        q = (State.id == state_code.lower() + district_number)

    state = State.select().where(q).get()
    ap_call = 'r' if romney_data['ap_winner'] else 'd' if obama_data['ap_winner'] else 'u'

    ap_called_at = state.ap_called_at

    if ap_call != state.ap_call:
        ap_called_at = datetime.datetime.now(tz=pytz.utc)

    state.ap_call = ap_call
    state.ap_called_at = ap_called_at
    state.total_precincts = race_data['total_precincts']
    state.precincts_reporting = race_data['precincts_reporting']
    state.rep_vote_count = romney_data['vote_count']
    state.dem_vote_count = obama_data['vote_count']

    state.save()


def bootstrap_senate_times():
    bootstrap_times(time_zones.SENATE_TIMES)


def bootstrap_house_times():
    bootstrap_times(time_zones.HOUSE_TIMES)


def bootstrap_times(times):
    for time_zone in times:
        obj = datetime.datetime.utcfromtimestamp(time_zone['time'])
        for district in time_zone['districts']:
            race_district = int(district.split(' ')[1].strip())
            race_state = district.split(' ')[0].strip().upper()

            race = Race.select().where(
                Race.district_id == race_district,
                Race.state_postal == race_state
            ).get()

            race.poll_closing_time = obj
            race.save()


def bootstrap_president():
    """
    Creates/overwrites presidential state results with initial data.
    """
    with open('initial_data/president_bootstrap.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for field in ['total_precincts', 'precincts_reporting', 'rep_vote_count', 'dem_vote_count']:
                if row[field] == '':
                    row[field] = 0
            try:
                state = State.select().where(
                    State.id == row['id']
                ).get()
                state.update(**row)
            except State.DoesNotExist:
                state = State.create(**row)

            state.save()


def update_polls():
    pollster = Pollster()

    for state in State.select().where(State.electoral_votes > 1):
        charts = pollster.charts(topic='2012-president', state=state.id)

        if charts:
            chart = charts[0]
        else:
            print 'NO DATA FOR %s' % state.id.upper()
            continue

        obama = 0
        romney = 0

        if chart.estimates:
            for estimate in chart.estimates:
                if estimate['choice'] == "Obama":
                    obama = estimate['value']
                elif estimate['choice'] == "Romney":
                    romney = estimate['value']
        else:
            print 'NO ESTIMATES FOR %s' % state.id.upper()
            continue

        prediction = "t"

        if abs(obama - romney) > 15:
            if obama > romney:
                prediction = "sd"
            else:
                prediction = "sr"
        elif abs(obama - romney) > 7.5:
            if obama > romney:
                prediction = "ld"
            else:
                prediction = "lr"

        uq = State.update(prediction=prediction).where(State.id == state)
        uq.execute()
