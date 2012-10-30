#!/usr/bin/env python

import json
import os
import gzip
import shutil
import boto
import time
import datetime
from datetime import timedelta

from itertools import combinations
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


def write_president_json():
    """
    Outputs the president json file for bigboard's frontend.
    """
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
                        timezone_dict['states'].append(state_dict)
            objects.append(timezone_dict)
        f.write(json.dumps(objects))


def _generate_json(house):
    """
    Generates JSON from rows of candidates and a house of congress.
    * House is a two-tuple ('house', 'H'), e.g., URL slug and DB representation.
    """
    objects = []
    now = datetime.datetime(2012, 11, 7, 1, 30)

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
                # close_time = district.poll_closing_time - timedelta(hours=5)
                # district_dict['status_tag'] = 'Poll closing time.'
                # district_dict['status'] = close_time.strftime('%I:%M').lstrip('0')
                district_dict['status_tag'] = 'Poll closing time.'
                district_dict['status'] = ''

            if district.poll_closing_time < now:
                if district_dict['called'] == True:
                    etnow = now - timedelta(hours=5)
                    district_dict['status_tag'] = 'Called time.'
                    district_dict['status'] = etnow.strftime('%I:%M').lstrip('0')
                else:
                    district_dict['status_tag'] = 'Percent reporting.'
                    district_dict['status'] = district.percent_reporting()

            district_dict['swap'] = False

            for candidate in Candidate.select().where(
                Candidate.race == district):
                    if (
                        candidate.party == u'Dem'
                        or candidate.party == u'GOP'
                        or candidate.first_name == 'Angus'):
                            candidate_dict = candidate._data

                            if candidate_dict['party'] == 'NPA':
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
    Rewrites CSV files from the DB for president.
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


def is_subset(combos_so_far, new_combo):
    """
    A general-purposed function for checking if this combo is a subset of another.
    """
    for old_combo in combos_so_far:
        test = new_combo[:len(old_combo['combo'])]

        if old_combo['combo'] == test:
            return True

    return False


def compute_combos(undecided_states, red_needs, blue_needs):
    """
    A general-purpose function for computing presidential path combos.
    """
    combos = []
    n = 1

    while n < len(undecided_states) + 1:
        combos.extend(combinations(undecided_states, n))
        n += 1

    red_combos = []
    blue_combos = []
    red_groups = {}
    blue_groups = {}

    for combo in combos:
        combo_votes = sum([state.electoral_votes for state in combo])
        combo = [state.id for state in combo]

        if combo_votes >= red_needs and not is_subset(red_combos, combo):
            combo_obj = {
                'combo': combo,
                'votes': combo_votes
            }

            key = len(combo)

            if key not in red_groups:
                red_groups[key] = []

            red_combos.append(combo_obj)
            red_groups[key].append(combo_obj)

        if combo_votes >= blue_needs and not is_subset(blue_combos, combo):
            combo_obj = {
                'combo': combo,
                'votes': combo_votes
            }

            key = len(combo)

            if key not in blue_groups:
                blue_groups[key] = []

            blue_combos.append(combo_obj)
            blue_groups[key].append(combo_obj)

    return {
        'undecided_states': [state.id for state in undecided_states],
        'red_combos': red_combos,
        'blue_combos': blue_combos,
        'red_groups': red_groups,
        'blue_groups': blue_groups
    }


