#!/usr/bin/env python

import json
import os
import gzip
import shutil
import boto
import time
import pytz
import datetime

from boto.s3.key import Key

import cms_settings as settings

from initial_data import time_zones
from models import Race, Candidate, State

utc = pytz.timezone('UTC')
eastern = pytz.timezone('US/Eastern')


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
    majority = data['needed_for_majority'] - votes
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


def calculate_senate_bop(race, data):
    """
    "total": The total number of seats held by this party.
        Math: Seats held over (below) + seats won tonight
    "needed_for_majority": The number of seats needed to have a majority.
        Math: 51 (majority share) - total.
    "total_pickups": The zero-indexed total number of pickups by this party.
        Math: Add one for each pickup by this party.
    """
    data['total'] += 1
    majority = 51 - data['total']
    if majority < 0:
        majority = 0
    data['needed_for_majority'] = majority

    if race.has_flipped:
        data['total_pickups'] += 1

    return data


def calculate_net_pickups(race, data):
    """
    Calculate the net pickups for this race.
    Needs to happen outside of the party loop since I have to assign pickups
    to both the winner (+1) and the loser (-1).
    """
    # See if this race has, in fact, flipped.
    if race.has_flipped == True:

        # race.flipped returns a tuple (winner, loser).
        # The winner/loser names match the dictionary keys.
        # Yaaaay!
        data[race.flipped[0]]['net_pickups'] += 1
        data[race.flipped[1]]['net_pickups'] -= 1

    return data


def bootstrap_bop_data():
    """
    Sets up the data structure for the balance of power calculations.
    """
    return {
        'house': {
            'democrats': {'total': 0, 'needed_for_majority': 218},
            'republicans': {'total': 0, 'needed_for_majority': 218},
            'other': {'total': 0, 'needed_for_majority': 218},
            'not_called': 0
        },
        'senate': {
            'democrats': {'total': 30, 'needed_for_majority': 21, 'net_pickups': 0, 'total_pickups': 0},
            'republicans': {'total': 37, 'needed_for_majority': 14, 'net_pickups': 0, 'total_pickups': 0},
            'other': {'total': 0, 'needed_for_majority': 0, 'net_pickups': 0, 'total_pickups': 0},
            'not_called': 0
        },
        'president': {
            'democrats': {'total': 0, 'needed_for_majority': 270},
            'republicans': {'total': 0, 'needed_for_majority': 270}
        }
    }


def produce_bop_json():
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
                        data[office][party] = calculate_senate_bop(race, data[office][party])

            if short == 'S':
                data[office] = calculate_net_pickups(race, data[office])

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

    return data


def write_bop_json():
    """
    Writes BOP json to files.
    """
    data = produce_bop_json()
    with open('www/bop.json', 'w') as f:
        f.write(json.dumps(data))
    with open('www/bop_jsonp.json', 'w') as f:
        f.write('balanceOfPower(%s)' % json.dumps(data))


def write_president_json():
    """
    Outputs the president json file for bigboard's frontend.
    """

    data = {}
    data['balance_of_power'] = produce_bop_json()
    data['results'] = []

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

                    call_time = None
                    if state_dict['called_at'] != None:
                        call_time = datetime.datetime.strptime(state_dict['called_at'].split('+')[0], '%Y-%m-%d %H:%M:%S.%f')
                        call_time = utc.normalize(utc.localize(call_time))

                    if state_dict['called_at'] != None:
                        state_dict['status_tag'] = 'Called time.'
                        state_dict['status'] = call_time.astimezone(eastern).strftime('%I:%M').lstrip('0')
                    else:
                        if state.precincts_reporting > 0:
                            state_dict['status_tag'] = 'Percent reporting.'
                            pct = state.percent_reporting()

                            if pct < 1:
                                state_dict['status'] = u'< 1%'
                            elif pct > 99 and pct < 100:
                                state_dict['status'] = u'99%'
                            else:
                                state_dict['status'] = u'%.0f%%' % pct
                        else:
                            state_dict['status_tag'] = 'No precincts reporting.'
                            if state_dict['dem_vote_count'] + state_dict['rep_vote_count'] > 0:
                                state_dict['status'] = u'< 1%'
                            else:
                                state_dict['status'] = u'&nbsp;'

                    timezone_dict['states'].append(state_dict)
            timezone_dict['states'] = sorted(timezone_dict['states'], key=lambda state: state['name'])
        data['results'].append(timezone_dict)

    with open('www/president.json', 'w') as f:
        f.write(json.dumps(data))


def _generate_json(house):
    """
    Generates JSON from rows of candidates and a house of congress.
    * House is a two-tuple ('house', 'H'), e.g., URL slug and DB representation.
    """
    data = {}
    data['balance_of_power'] = produce_bop_json()
    data['results'] = []

    for timezone in settings.CLOSING_TIMES:
        timezone_dict = {}
        timezone_dict['gmt_epoch_time'] = time.mktime(timezone.timetuple())
        timezone_dict['districts'] = []

        races = Race.select().where(
            Race.office_code == house[1],
            Race.poll_closing_time == timezone,
            Race.featured_race == True)

        for district in races:

            # Set up the race information.
            district_dict = {}
            district_dict['district'] = u'%s %s' % (
                district.state_postal,
                district.district_id)
            district_dict['sorter'] = (district.state_postal, district.district_id)
            district_dict['candidates'] = []
            district_dict['district_slug'] = district.slug

            # Percent reporting.
            district_dict['percent_reporting'] = district.percent_reporting()

            # Call times.
            district_dict['called_time'] = None
            if district.accept_ap_call == True:
                district_dict['called'] = district.ap_called
                if district.ap_called_time != None:
                    call_time = utc.normalize(utc.localize(district.ap_called_time))
                    call_time = call_time.astimezone(eastern)
                    district_dict['called_time'] = call_time.strftime('%I:%M').lstrip('0')
            elif district.accept_ap_call == False:
                district_dict['called'] = district.npr_called
                if district.npr_called_time != None:
                    call_time = utc.normalize(utc.localize(district.npr_called_time))
                    call_time = call_time.astimezone(eastern)
                    district_dict['called_time'] = call_time.strftime('%I:%M').lstrip('0')

            # Status field.
            if district_dict['called'] == True:
                district_dict['status_tag'] = 'Called time.'
                district_dict['status'] = district_dict['called_time']
            else:
                if district.precincts_reporting > 0:
                    district_dict['status_tag'] = 'Percent reporting.'
                    pct = district.percent_reporting()

                    if pct < 1:
                        district_dict['status'] = u'< 1%'
                    elif pct > 99 and pct < 100:
                        district_dict['status'] = u'99%'
                    else:
                        district_dict['status'] = u'%.0f%%' % district.percent_reporting()
                else:
                    district_dict['status_tag'] = 'No precincts reporting.'
                    if district.total_votes() > 0:
                        district_dict['status'] = u'< 1%'
                    else:
                        district_dict['status'] = u'&nbsp;'
            # Flips.
            district_dict['swap'] = False
            if district.has_flipped:
                if district.flipped[0]:
                    district_dict['swap'] = True

            # Candidates.
            for candidate in Candidate.select().where(Candidate.race == district):
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

                        # By default, all candidates are not swaps.
                        candidate_dict['swap'] = False

                        # First, check if there's a winner. Can't have a swap
                        # without a winner.
                        if candidate_dict['winner'] == True:

                            # Hardcoding an edge-case for IA3 and OH16.
                            if district_dict['district_slug'] == 'ia3':
                                candidate_dict['swap'] = True

                            if district_dict['district_slug'] == 'oh16':
                                candidate_dict['swap'] = True

                            # Second, check if this is the incumbent. Can't have
                            # an incumbent win AND this be a swap.
                            if candidate_dict['incumbent'] == False:

                                # The first swap type is the easiest.
                                # If there IS an incumbent AND this candidate
                                # isn't the incumbent, then there's a swap.

                                if district.has_incumbents() == True:
                                    candidate_dict['swap'] = True

                                # The second swap type is slightly harder.
                                # If there isn't an incumbent but there IS a
                                # predicted winner (e.g., seat held by a party)
                                # and this candidate's party doesn't match the
                                # prediction, then there's a swap.
                                else:
                                    if candidate_dict['party'] == 'GOP':
                                        party = u'republicans'
                                    elif candidate_dict['party'] == 'Dem':
                                        party = u'democrats'
                                    else:
                                        party = u'other'

                                    if district.flipped[0]:
                                        if party == district.flipped[0]:
                                            candidate_dict['swap'] = True

                        district_dict['called_time'] = None

                        if candidate.last_name != 'Dill':
                            district_dict['candidates'].append(
                                candidate_dict)

            district_dict['candidates'] = sorted(
                district_dict['candidates'],
                key=lambda candidate: candidate['party'])

            timezone_dict['districts'].append(district_dict)

        timezone_dict['districts'] = sorted(
            timezone_dict['districts'],
            key=lambda district: district['sorter'])

        if races.count() > 1:
            data['results'].append(timezone_dict)

    return json.dumps(data)


def write_house_json():
    """
    Calls generate_json() to build the house json file.
    """
    output = _generate_json((u'house', u'H'))

    with open(settings.HOUSE_FILENAME, 'w') as f:
        f.write(output)


def write_senate_json():
    """
    Calls generate_json to build the senatejson file.
    """
    output = _generate_json((u'senate', u'S'))

    with open(settings.SENATE_FILENAME, 'w') as f:
        f.write(output)


def write_electris_json():
    """
    Rewrites JSON files from the DB for president.
    """
    output_states = []

    for state in State.select().order_by(State.electoral_votes.desc(), State.name.asc()):
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

        output_states.append(state)

    output = json.dumps({
        'balance_of_power': produce_bop_json(),
        'states': output_states
    })

    with open(settings.PRESIDENT_FILENAME, 'w') as f:
        f.write(output)


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
