#!/usr/bin/env python

import csv
import json
import os
import gzip
import shutil
import boto
import time
from boto.s3.key import Key
import cms_settings as settings

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


# def write_president_json(states):
#     with open('www/president.json', 'w') as f:
#         times = settings.PRESIDENT_TIMES
#         objects = []
#         for timezone in times:
#             timezone_dict = {}
#             timezone_dict['gmt_epoch_time'] = timezone['time']
#             timezone_dict['states'] = []
#             for s in timezone['states']:
#                 for state in states:
#                     if state['id'].upper() == s:
#                         timezone_dict['states'].append(dict(state))
#             objects.append(timezone_dict)
#         f.write(json.dumps(objects))


def write_house_json():
    with open(settings.HOUSE_FILENAME, 'w') as f:
        f.write(generate_json((u'house', u'H')))


def write_senate_json():
    with open(settings.SENATE_FILENAME, 'w') as f:
        f.write(generate_json((u'senate', u'S')))


def generate_json(house):
    """
    Generates JSON from rows of candidates and a house of congress.
    * Rows should be an iterator. In this case, a query for candidates.
    * House should be a two-tuple: ('house', 'h').
    """
    objects = []
    for timezone in settings.CLOSING_TIMES:
        timezone_dict = {}
        timezone_dict['gmt_epoch_time'] = time.mktime(timezone.timetuple())
        timezone_dict['districts'] = []

        for district in Race.select().where(
            Race.office_code == house[1],
            Race.poll_closing_time == timezone):

            district_dict = {}
            district_dict['district'] = u'%s %s' % (
                district.state_postal,
                district.district_id)
            district_dict['candidates'] = []
            district_dict['district_slug'] = district.slug

            if district.accept_ap_call == True:
                district_dict['called'] = district.ap_called
                district_dict['called_time'] = district.ap_called_time
            elif district.accept_ap_call == False:
                district_dict['called'] = district.npr_called
                district_dict['called_time'] = district.npr_called_time

            for candidate in Candidate.select().where(
                Candidate.race == district):
                    if (
                        candidate.party == u'Dem'
                        or candidate.party == u'GOP'
                        or candidate.first_name == 'Angus'):
                            candidate_dict = candidate._data
                            candidate_dict['winner'] = False

                            if district.accept_ap_call == True:
                                if candidate_dict['ap_winner'] == True:
                                    candidate_dict['winner'] = True
                            else:
                                if candidate_dict['npr_winner'] == True:
                                    candidate_dict['winner'] = True

                            district_dict['called_time'] = None

                            if candidate.last_name != 'Dill':
                                district_dict['candidates'].append(
                                    candidate_dict)

            district_dict['candidates'] = sorted(
                district_dict['candidates'],
                key=lambda candidate: candidate['party'])

            timezone_dict['districts'].append(district_dict)

        objects.append(timezone_dict)

    return json.dumps(objects)


def regenerate_president():
    """
    Rewrites CSV files from the DB for president.
    """
    with open(settings.PRESIDENT_FILENAME, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(settings.PRESIDENT_HEADER)

        for state in State.select():
            state = state._data

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
