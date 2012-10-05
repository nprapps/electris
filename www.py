#!/usr/bin/env python

from datetime import datetime
import json
from sets import Set

from flask import Flask
from flask import render_template, request
import pytz

import cms_settings as settings
from util import (
    get_database, get_states, regenerate_csv, push_results_to_s3, get_house_candidates, get_senate_candidates)
from fetch_ap_results import CANDIDATE_MODEL_FIELDS

app = Flask(__name__)

@app.route('/', methods=['GET'])
def race_list():
    """
    Return a list of races in case someone gets to the main page.
    """

    return """
        <html>
            <body>
                <h1>RACES</h1>
                <a href='/house/www/'>HOUSE</a><br/>
                <a href='/senate/www/'>SENATE</a>
            </body>
        </html>
    """

@app.route('/house/www/', methods=['GET'])
def house_candidates():
    """
    Read/update list of results-by-district for the U.S. House election.
    This is limited to the "state_candidates" table in the SQLite DB.
    """
    db = get_database()
    candidates_query = get_house_candidates(db)
    db.close()

    districts = Set([])
    districts_list = []

    for candidate in candidates_query:
        candidate_dict = dict(zip(CANDIDATE_MODEL_FIELDS, candidate))
        district_string = '%s %s' % (
            candidate_dict['state_id'].upper(),
            candidate_dict['race'].replace('District', '').strip()
        )
        districts.add(district_string)

    for district in sorted(districts, key=lambda district: (district.split(' ')[0], int(district.split(' ')[1]))):
        state = district.split(' ')[0].strip().lower()
        race = 'District %s' % district.split(' ')[1].strip()
        district_dict = {}
        district_dict['name'] = district
        district_dict['candidates'] = []
        for candidate in candidates_query:
            candidate_dict = dict(zip(CANDIDATE_MODEL_FIELDS, candidate))
            if (candidate_dict['state_id'] == state) and (candidate_dict['race'] == race):
                district_dict['candidates'].append(candidate_dict)
        districts_list.append(district_dict)

    context = {
        'settings': settings,
        'districts': districts_list,
        'race': 'U.S. House'
    }

    return render_template('house_senate_www.html', **context)

@app.route('/senate/www/', methods=['GET'])
def senate_candidates():
    """
    Read/update list of results-by-district for the U.S. House election.
    This is limited to the "state_candidates" table in the SQLite DB.
    """
    db = get_database()
    candidates_query = get_senate_candidates(db)
    db.close()

    districts = Set([])
    districts_list = []

    for candidate in candidates_query:
        candidate_dict = dict(zip(CANDIDATE_MODEL_FIELDS, candidate))
        district_string = '%s %s' % (
            candidate_dict['state_id'].upper(),
            candidate_dict['race'].replace('District', '').strip()
        )
        districts.add(district_string)

    for district in sorted(districts, key=lambda district: (district.split(' ')[0], int(district.split(' ')[1]))):
        state = district.split(' ')[0].strip().lower()
        race = 'District %s' % district.split(' ')[1].strip()
        district_dict = {}
        district_dict['name'] = district
        district_dict['candidates'] = []
        for candidate in candidates_query:
            candidate_dict = dict(zip(CANDIDATE_MODEL_FIELDS, candidate))
            if (candidate_dict['state_id'] == state) and (candidate_dict['race'] == race):
                district_dict['candidates'].append(candidate_dict)
        districts_list.append(district_dict)

    context = {
        'settings': settings,
        'districts': districts_list,
        'race': 'U.S. Senate'
    }

    return render_template('house_senate_www.html', **context)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=settings.DEBUG)
