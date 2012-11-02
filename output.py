#!/usr/bin/env python

import json
import os
import gzip
import shutil
import boto
import time
import datetime

from datetime import timedelta
from boto.s3.key import Key

import cms_settings as settings

from initial_data import time_zones
from models import Race, Candidate, State


def gzip_www():
    """
    Moved from gzip_www.py.
    Note: Contains a hack to override gzip's time implementation.
    See http://bit.ly/4jnfH for details.
    """
    class FakeTime:
        def time(self):
            return 1261130520.0

    gzip.time = FakeTime()

    shutil.rmtree('gzip', ignore_errors=True)
    shutil.copytree('www', 'gzip')

    for path, dirs, files in os.walk('gzip'):
        for filename in files:
            file_path = os.path.join(path, filename)

            f_in = open(file_path, 'rb')
            contents = f_in.readlines()
            f_in.close()

            f_out = gzip.open(file_path, 'wb')
            f_out.writelines(contents)
            f_out.close()


def calculate_president_bop(data, votes):
    """
    A function for calculating the presidential balance-of-power.
    """
    data['total'] += votes
    majority = data['needed_for_majority'] - 1
    if majority < 0:
        majority = 0
    data['needed_for_majority'] = majority
    return data


def calculate_house_bop(data):
    data['total'] += 1
    majority = data['needed_for_majority'] - 1
    if majority < 0:
        majority = 0
    data['needed_for_majority'] = majority
    return data


def calculate_senate_bop(data):
    data['total'] += 1
    data['delta'] += 1
    majority = 51 - data['delta']
    if majority < 0:
        majority = 0
    data['needed_for_majority'] = majority
    return data


def bootstrap_bop_data():
    """
    Sets up the data structure for the balance of power calculations.
    """
    return {
        'house': {
            'democrats': {'total': 0, 'needed_for_majority': 218, 'delta': 0},
            'republicans': {'total': 0, 'needed_for_majority': 218, 'delta': 0},
            'other': {'total': 0, 'needed_for_majority': 218, 'delta': 0},
            'not_called': 0
        },
        'senate': {
            'democrats': {'total': 0, 'needed_for_majority': 0, 'delta': 30},
            'republicans': {'total': 0, 'needed_for_majority': 0, 'delta': 37},
            'other': {'total': 0, 'needed_for_majority': 0, 'delta': 2},
            'not_called': 0
        },
        'president': {
            'democrats': {'total': 0, 'needed_for_majority': 270},
            'republicans': {'total': 0, 'needed_for_majority': 270}
        }
    }


def write_bop_json():
    """
    Loops through houses/parties to count seats and calculate deltas.
    """
    # Party mapping.
    parties = [('republicans', 'r'), ('democrats', 'd'), ('other', 'o')]

    # House/seats/delta mapping.
    houses = [('house', 'H'), ('senate', 'S')]

    # Blank dataset.
    data = bootstrap_bop_data()

    # President.
    for state in State.select().where(State.called == True):
        for party, abbr in parties:
            if state.winner == abbr:
                data['president'][party] = calculate_president_bop(data['president'][party], state.electoral_votes)

    # House/senate.
    for office, short in houses:
        for race in Race.select().where(
            (Race.ap_called == True) | (Race.npr_called == True), Race.office_code == short):
            for party, abbr in parties:
                if race.winner == abbr:
                    if short == 'H':
                        data[office][party] = calculate_house_bop(data[office][party])
                    if short == 'S':
                        data[office][party] = calculate_senate_bop(data[office][party])

        # Write the number of uncalled races.
        # First, the races where we accept AP calls but no calls have come in.
        data[office]['not_called'] += Race.select()\
            .where(
                Race.accept_ap_call == True,
                Race.ap_called == False,
                Race.office_code == short)\
            .count()

        # Second, the races where we don't accept AP calls and no NPR calls are in.
        data[office]['not_called'] += Race.select()\
            .where(
                Race.accept_ap_call == False,
                Race.npr_called == False,
                Race.office_code == short)\
            .count()

    with open('www/bop.json', 'w') as f:
        f.write(json.dumps(data))

    with open('www/bop_jsonp.json', 'w') as f:
        f.write('balanceOfPower(%s)' % data)


def write_president_json():
    """
    Outputs the president json file for bigboard's frontend.
    """
    now = datetime.datetime.now()

    with open('www/president.json', 'w') as f:
        objects = []
        for timezone in time_zones.PRESIDENT_TIMES:
            timezone_dict = {}
            timezone_dict['gmt_epoch_time'] = timezone['time']
            timezone_dict['states'] = []
            for s in timezone['states']:
                for state in State.select():
                    if state.id == s.lower():
                        state_dict = state._data
                        state_dict['rep_vote_percent'] = state.rep_vote_percent()
                        state_dict['dem_vote_percent'] = state.dem_vote_percent()
                        state_dict['human_gop_vote_count'] = state.human_rep_vote_count()
                        state_dict['human_dem_vote_count'] = state.human_dem_vote_count()
                        state_dict['called'] = state.called
                        state_dict['winner'] = state.winner

                        if state_dict['npr_call'] != 'n' and state_dict['npr_call'] != 'u':
                            state_dict['call'] = state_dict['npr_call']
                            state_dict['called_at'] = state_dict['npr_called_at']
                            state_dict['called_by'] = 'npr'
                        elif state_dict['accept_ap_call'] and state_dict['ap_call'] != 'u':
                            state_dict['call'] = state_dict['ap_call']
                            state_dict['called_at'] = state_dict['ap_called_at']
                            state_dict['called_by'] = 'ap'
                        else:
                            state_dict['call'] = None
                            state_dict['called_at'] = None
                            state_dict['called_by'] = None

                        etnow = now - timedelta(hours=5)
                        call_time = None
                        if state_dict['called_at'] != None:
                            call_time = datetime.datetime.strptime(state_dict['called_at'].split('+')[0], '%Y-%m-%d %H:%M:%S.%f')

                        if datetime.datetime.fromtimestamp(timezone['time']) > etnow:
                            if state_dict['called_at'] != None:
                                state_dict['status_tag'] = 'Called time.'
                                state_dict['status'] = call_time.strftime('%I:%M').lstrip('0')
                            else:
                                state_dict['status_tag'] = 'Poll closing time.'
                                state_dict['status'] = '&nbsp;'

                        if datetime.datetime.fromtimestamp(timezone['time']) < etnow:
                            if state_dict['called_at'] != None:
                                state_dict['status_tag'] = 'Called time.'
                                state_dict['status'] = call_time.strftime('%I:%M').lstrip('0')
                            else:
                                state_dict['status_tag'] = 'Percent reporting.'
                                state_dict['status'] = u'%s' % state.percent_reporting()

                        timezone_dict['states'].append(state_dict)
            objects.append(timezone_dict)
        f.write(json.dumps(objects))


def _generate_json(house):
    """
    Generates JSON from rows of candidates and a house of congress.
    * House is a two-tuple ('house', 'H'), e.g., URL slug and DB representation.
    """
    objects = []
    now = datetime.datetime.now()

    for timezone in settings.CLOSING_TIMES:
        timezone_dict = {}
        timezone_dict['gmt_epoch_time'] = time.mktime(timezone.timetuple())
        timezone_dict['districts'] = []

        races = Race.select().where(
            Race.office_code == house[1],
            Race.poll_closing_time == timezone,
            Race.featured_race == True)

        for district in races:

            district_dict = {}
            district_dict['district'] = u'%s %s' % (
                district.state_postal,
                district.district_id)
            district_dict['candidates'] = []
            district_dict['district_slug'] = district.slug

            district_dict['percent_reporting'] = district.percent_reporting()

            if district.accept_ap_call == True:
                district_dict['called'] = district.ap_called
                district_dict['called_time'] = district.ap_called_time
            elif district.accept_ap_call == False:
                district_dict['called'] = district.npr_called
                district_dict['called_time'] = district.npr_called_time

            if district.poll_closing_time > now:
                if district_dict['called'] == True:
                    etnow = now - timedelta(hours=5)
                    district_dict['status_tag'] = 'Called time.'
                    district_dict['status'] = etnow.strftime('%I:%M').lstrip('0')
                else:
                    district_dict['status_tag'] = 'Poll closing time.'
                    district_dict['status'] = '&nbsp;'

            if district.poll_closing_time < now:
                if district_dict['called'] == True:
                    etnow = now - timedelta(hours=5)
                    district_dict['status_tag'] = 'Called time.'
                    district_dict['status'] = etnow.strftime('%I:%M').lstrip('0')
                else:
                    district_dict['status_tag'] = 'Percent reporting.'
                    district_dict['status'] = u'%s' % district.percent_reporting()

            district_dict['swap'] = False

            for candidate in Candidate.select().where(
                Candidate.race == district):
                    if (
                    candidate.party == u'Dem'
                    or candidate.party == u'GOP'
                    or candidate.first_name == 'Angus'
                    or candidate.first_name == 'Bernie'):
                        candidate_dict = candidate._data

                        if (candidate_dict['party'] == 'NPA'
                        or candidate_dict['party'] == 'Ind'):
                            candidate_dict['party'] = 'Alt'

                        candidate_dict['vote_percent'] = candidate.vote_percent()
                        candidate_dict['winner'] = False

                        if district.accept_ap_call == True:
                            if candidate_dict['ap_winner'] == True:
                                candidate_dict['winner'] = True
                        else:
                            if candidate_dict['npr_winner'] == True:
                                candidate_dict['winner'] = True

                        candidate_dict['swap'] = False
                        if candidate_dict['winner'] == True:
                            if candidate_dict['incumbent'] == False:
                                candidate_dict['swap'] = True
                                district_dict['swap'] = True

                        district_dict['called_time'] = None

                        if candidate.last_name != 'Dill':
                            district_dict['candidates'].append(
                                candidate_dict)

            district_dict['candidates'] = sorted(
                district_dict['candidates'],
                key=lambda candidate: candidate['party'])

            timezone_dict['districts'].append(district_dict)

        if races.count() > 1:
            objects.append(timezone_dict)

    return json.dumps(objects)


def write_house_json():
    """
    Calls generate_json() to build the house json file.
    """
    with open(settings.HOUSE_FILENAME, 'w') as f:
        f.write(_generate_json((u'house', u'H')))


def write_senate_json():
    """
    Calls generate_json to build the senatejson file.
    """
    with open(settings.SENATE_FILENAME, 'w') as f:
        f.write(_generate_json((u'senate', u'S')))


def write_electris_json():
    """
    Rewrites JSON files from the DB for president.
    """
    with open(settings.PRESIDENT_FILENAME, 'w') as f:
        output = []

        for state in State.select().order_by(State.electoral_votes.desc()):
            state = state._data

            if state['npr_call'] != 'n' and state['npr_call'] != 'u':
                state['call'] = state['npr_call']
                state['called_at'] = state['npr_called_at']
                state['called_by'] = 'npr'
            elif state['accept_ap_call'] and state['ap_call'] != 'u':
                state['call'] = state['ap_call']
                state['called_at'] = state['ap_called_at']
                state['called_by'] = 'ap'
            else:
                state['call'] = None
                state['called_at'] = None
                state['called_by'] = None

            del state['npr_call']
            del state['npr_called_at']
            del state['ap_call']
            del state['ap_called_at']

            del state['called_by']
            del state['accept_ap_call']
            del state['rowid']
            del state['prediction']

            output.append(state)

        f.write(json.dumps(output))


def push_results_to_s3():
    """
    Push president and house/senate CSV files to S3.
    """
    conn = boto.connect_s3()
    bucket = conn.get_bucket(settings.S3_BUCKET)
    headers = {'Cache-Control': 'max-age=0 no-cache no-store must-revalidate'}
    policy = 'public-read'

    if os.path.exists(settings.PRESIDENT_FILENAME):
        president_key = Key(bucket)
        president_key.key = settings.PRESIDENT_S3_KEY
        president_key.set_contents_from_filename(
            settings.PRESIDENT_FILENAME,
            policy=policy,
            headers=headers)

    if os.path.exists(settings.PRESIDENT_JSON_FILENAME):
        president_json = Key(bucket)
        president_json.key = settings.PRESIDENT_JSON_S3_KEY
        president_json.set_contents_from_filename(
            settings.PRESIDENT_JSON_FILENAME,
            policy=policy,
            headers=headers)

    if os.path.exists(settings.HOUSE_FILENAME):
        house_key = Key(bucket)
        house_key.key = settings.HOUSE_S3_KEY
        house_key.set_contents_from_filename(
            settings.HOUSE_FILENAME,
            policy=policy,
            headers=headers)

    if os.path.exists(settings.SENATE_FILENAME):
        senate_key = Key(bucket)
        senate_key.key = settings.SENATE_S3_KEY
        senate_key.set_contents_from_filename(
            settings.SENATE_FILENAME,
            policy=policy,
            headers=headers)

