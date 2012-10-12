#!/usr/bin/env python

import datetime

# Project settings.
PROJECT_NAME = 'electris'
DATABASE_FILENAME = 'electris.db'
POLLING_INTERVAL = 15

# Constants for Electris the Web app.
PRESIDENT_HEADER = ['id', 'stateface', 'name', 'abbr', 'electoral_votes', 'polls_close', 'prediction', 'call', 'called_at', 'called_by', 'total_precincts', 'precincts_reporting', 'rep_vote_count', 'dem_vote_count']
PREDICTION_OPTIONS = [('sd', 'Solid Democrat'), ('ld', 'Leaning Democrat'), ('t', 'Tossup'), ('lr', 'Leaning Republican'), ('sr', 'Solid Republican')]
RESULT_OPTIONS = [('d', 'Democrat'), ('u', 'Undecided'), ('r', 'Republican')]

# Constants for the BigBoard Web app.
HOUSE_SENATE_HEADER = [
    'state_postal',
    'state_name',
    'office_code',
    'district_id',
    'office_name',
    'district_name',
    'precincts_reporting',
    'total_precincts',
    'ap_npid',
    'first_name',
    'last_name',
    'middle_name',
    'junior',
    'use_junior',
    'incumbent',
    'party',
    'vote_count',
    'ap_winner',
    'ap_winner_time',
    'npr_winner',
    'npr_winner_time',
    'accept_ap_call',
    'race_slug'
]
SENATE_TIMES = [
    {'time': 1352246400, 'districts': ['IN 0', 'VA 0', 'VT 0']},
    {'time': 1352248200, 'districts': ['OH 0', 'WV 0']},
    {'time': 1352250000, 'districts': ['CT 0', 'DE 0', 'FL 0', 'MA 0', 'MD 0', 'ME 0', 'MO 0', 'MS 0 ', 'NJ 0', 'PA 0', 'RI 0', 'TN 0']},
    {'time': 1352253600, 'districts': ['AZ 0', 'MI 0 ', 'MN 0', 'ND 0', 'NE 0', 'NM 0', 'NY 0', 'TX 0', 'WI 0', 'WY 0']},
    {'time': 1352257200, 'districts': ['MT 0', 'NV 0', 'UT 0']},
    {'time': 1352260800, 'districts': ['CA 0', 'HI 0', 'WA 0']}
]
# HOUSE_TIMES = [
#     {'time': 1352246400, 'districts': ['GA 1', 'GA 2', 'GA 3', 'GA 4', 'GA 5', 'GA 6', 'GA 7', 'GA 8', 'GA 9', 'GA 10', 'GA 11', 'GA 12', 'GA 13', 'GA 14', 'IN 1', 'IN 2', 'IN 3', 'IN 4', 'IN 5', 'IN 6', 'IN 7', 'IN 8', 'IN 9', 'KY 1', 'KY 2', 'KY 3', 'KY 4', 'KY 5', 'KY 6', 'SC 1', 'SC 2', 'SC 3', 'SC 4', 'SC 5', 'SC 6', 'SC 7', 'VA 1', 'VA 2', 'VA 3', 'VA 4', 'VA 5', 'VA 6', 'VA 7', 'VA 8', 'VA 9', 'VA 10', 'VA 11', 'VT 1']},
#     {'time': 1352248200, 'districts': ['NC 1', 'NC 2', 'NC 3', 'NC 4', 'NC 5', 'NC 6', 'NC 7', 'NC 8', 'NC 9', 'NC 10', 'NC 11', 'NC 12', 'NC 13', 'OH 1', 'OH 2', 'OH 3', 'OH 4', 'OH 5', 'OH 6', 'OH 7', 'OH 8', 'OH 9', 'OH 10', 'OH 11', 'OH 12', 'OH 13', 'OH 14', 'OH 15', 'OH 16', 'WV 1', 'WV 2', 'WV 3']},
#     {'time': 1352250000, 'districts': ['AL 1', 'AL 2', 'AL 3', 'AL 4', 'AL 5', 'AL 6', 'AL 7', 'CT 1', 'CT 2', 'CT 3', 'CT 4', 'CT 5', 'DE 1', 'FL 1', 'FL 2', 'FL 3', 'FL 4', 'FL 5', 'FL 6', 'FL 7', 'FL 8', 'FL 9', 'FL 10', 'FL 11', 'FL 12', 'FL 13', 'FL 14', 'FL 15', 'FL 16', 'FL 17', 'FL 18', 'FL 19', 'FL 20', 'FL 21', 'FL 22', 'FL 23', 'FL 24', 'FL 25', 'FL 26', 'FL 27', 'IL 1', 'IL 2', 'IL 3', 'IL 4', 'IL 5', 'IL 6', 'IL 7', 'IL 8', 'IL 9', 'IL 10', 'IL 11', 'IL 12', 'IL 13', 'IL 14', 'IL 15', 'IL 16', 'IL 17', 'IL 18', 'MA 1', 'MA 2', 'MA 3', 'MA 4', 'MA 5', 'MA 6', 'MA 7', 'MA 8', 'MA 9', 'MD 1', 'MD 2', 'MD 3', 'MD 4', 'MD 5', 'MD 6', 'MD 7', 'MD 8', 'ME 1', 'ME 2', 'MO 1', 'MO 2', 'MO 3', 'MO 4', 'MO 5', 'MO 6', 'MO 7', 'MO 8', 'MS 1', 'MS 2', 'MS 3', 'MS 4', 'NH 1', 'NH 2', 'NJ 1', 'NJ 2', 'NJ 3', 'NJ 4', 'NJ 5', 'NJ 6', 'NJ 7', 'NJ 8', 'NJ 9', 'NJ 10', 'NJ 11', 'NJ 12', 'OK 1', 'OK 2', 'OK 3', 'OK 4', 'OK 5', 'OR 1', 'OR 2', 'OR 3', 'OR 4', 'OR 5', 'PA 1', 'PA 2', 'PA 3', 'PA 4', 'PA 5', 'PA 6', 'PA 7', 'PA 8', 'PA 9', 'PA 10', 'PA 11', 'PA 12', 'PA 13', 'PA 14', 'PA 15', 'PA 16', 'PA 17', 'PA 18', 'RI 1', 'RI 2', 'TN 1', 'TN 2', 'TN 3', 'TN 4', 'TN 5', 'TN 6', 'TN 7', 'TN 8', 'TN 9']},
#     {'time': 1352251800, 'districts': ['AR 1', 'AR 2', 'AR 3', 'AR 4']},
#     {'time': 1352253600, 'districts': ['AZ 1', 'AZ 2', 'AZ 3', 'AZ 4', 'AZ 5', 'AZ 6', 'AZ 7', 'AZ 8', 'AZ 9', 'CO 1', 'CO 2', 'CO 3', 'CO 4', 'CO 5', 'CO 6', 'CO 7', 'KS 1', 'KS 2', 'KS 3', 'KS 4', 'LA 1', 'LA 2', 'LA 3', 'LA 4', 'LA 5', 'LA 6', 'MI 1', 'MI 2', 'MI 3', 'MI 4', 'MI 5', 'MI 6', 'MI 7', 'MI 8', 'MI 9', 'MI 10', 'MI 11', 'MI 12', 'MI 13', 'MI 14', 'MN 1', 'MN 2', 'MN 3', 'MN 4', 'MN 5', 'MN 6', 'MN 7', 'MN 8', 'ND 1', 'NE 1', 'NE 2', 'NE 3', 'NM 1', 'NM 2', 'NM 3', 'NY 1', 'NY 2', 'NY 3', 'NY 4', 'NY 5', 'NY 6', 'NY 7', 'NY 8', 'NY 9', 'NY 10', 'NY 11', 'NY 12', 'NY 13', 'NY 14', 'NY 15', 'NY 16', 'NY 17', 'NY 18', 'NY 19', 'NY 20', 'NY 21', 'NY 22', 'NY 23', 'NY 24', 'NY 25', 'NY 26', 'NY 27', 'SD 1', 'TX 1', 'TX 2', 'TX 3', 'TX 4', 'TX 5', 'TX 6', 'TX 7', 'TX 8', 'TX 9', 'TX 10', 'TX 11', 'TX 12', 'TX 13', 'TX 14', 'TX 15', 'TX 16', 'TX 17', 'TX 18', 'TX 19', 'TX 20', 'TX 21', 'TX 22', 'TX 23', 'TX 24', 'TX 25', 'TX 26', 'TX 27', 'TX 28', 'TX 29', 'TX 30', 'TX 31', 'TX 32', 'TX 33', 'TX 34', 'TX 35', 'TX 36', 'WI 1', 'WI 2', 'WI 3', 'WI 4', 'WI 5', 'WI 6', 'WI 7', 'WI 8', 'WY 1']},
#     {'time': 1352257200, 'districts': ['IA 1', 'IA 2', 'IA 3', 'IA 4', 'MT 1', 'NV 1', 'NV 2', 'NV 3', 'NV 4', 'UT 1', 'UT 2', 'UT 3', 'UT 4']},
#     {'time': 1352260800, 'districts': ['CA 1', 'CA 2', 'CA 3', 'CA 4', 'CA 5', 'CA 6', 'CA 7', 'CA 8', 'CA 9', 'CA 10', 'CA 11', 'CA 12', 'CA 13', 'CA 14', 'CA 15', 'CA 16', 'CA 17', 'CA 18', 'CA 19', 'CA 20', 'CA 21', 'CA 22', 'CA 23', 'CA 24', 'CA 25', 'CA 26', 'CA 27', 'CA 28', 'CA 29', 'CA 30', 'CA 31', 'CA 32', 'CA 33', 'CA 34', 'CA 35', 'CA 36', 'CA 37', 'CA 38', 'CA 39', 'CA 40', 'CA 41', 'CA 42', 'CA 43', 'CA 44', 'CA 45', 'CA 46', 'CA 47', 'CA 48', 'CA 49', 'CA 50', 'CA 51', 'CA 52', 'CA 53', 'HI 1', 'HI 2', 'ID 1', 'ID 2', 'WA 1', 'WA 2', 'WA 3', 'WA 4', 'WA 5', 'WA 6', 'WA 7', 'WA 8', 'WA 9', 'WA 10']},
#     {'time': 1352264400, 'districts': ['AK 1']}
# ]
HOUSE_TIMES = [
    {'time': 1352246400, 'districts': ['GA 1', 'GA 2', 'GA 3', 'GA 4', 'GA 5', 'GA 6', 'GA 7', 'GA 8', 'GA 9', 'GA 10', 'GA 11', 'GA 12', 'GA 13', 'GA 14', 'IN 1', 'IN 2', 'IN 3', 'IN 4', 'IN 5', 'IN 6', 'IN 7', 'IN 8', 'IN 9', 'KY 1', 'KY 2', 'KY 3', 'KY 4', 'KY 5', 'KY 6', 'SC 1', 'SC 2', 'SC 3', 'SC 4', 'SC 5', 'SC 6', 'SC 7', 'VA 1', 'VA 2', 'VA 3', 'VA 4', 'VA 5', 'VA 6', 'VA 7', 'VA 8', 'VA 9', 'VA 10', 'VA 11', 'VT 1']},
    # {'time': 1352248200, 'districts': ['NC 1', 'NC 2', 'NC 3', 'NC 4', 'NC 5', 'NC 6', 'NC 7', 'NC 8', 'NC 9', 'NC 10', 'NC 11', 'NC 12', 'NC 13', 'OH 1', 'OH 2', 'OH 3', 'OH 4', 'OH 5', 'OH 6', 'OH 7', 'OH 8', 'OH 9', 'OH 10', 'OH 11', 'OH 12', 'OH 13', 'OH 14', 'OH 15', 'OH 16', 'WV 1', 'WV 2', 'WV 3']},
    # {'time': 1352250000, 'districts': ['AL 1', 'AL 2', 'AL 3', 'AL 4', 'AL 5', 'AL 6', 'AL 7', 'CT 1', 'CT 2', 'CT 3', 'CT 4', 'CT 5', 'DE 1', 'FL 1', 'FL 2', 'FL 3', 'FL 4', 'FL 5', 'FL 6', 'FL 7', 'FL 8', 'FL 9', 'FL 10', 'FL 11', 'FL 12', 'FL 13', 'FL 14', 'FL 15', 'FL 16', 'FL 17', 'FL 18', 'FL 19', 'FL 20', 'FL 21', 'FL 22', 'FL 23', 'FL 24', 'FL 25', 'FL 26', 'FL 27', 'IL 1', 'IL 2', 'IL 3', 'IL 4', 'IL 5', 'IL 6', 'IL 7', 'IL 8', 'IL 9', 'IL 10', 'IL 11', 'IL 12', 'IL 13', 'IL 14', 'IL 15', 'IL 16', 'IL 17', 'IL 18', 'MA 1', 'MA 2', 'MA 3', 'MA 4', 'MA 5', 'MA 6', 'MA 7', 'MA 8', 'MA 9', 'MD 1', 'MD 2', 'MD 3', 'MD 4', 'MD 5', 'MD 6', 'MD 7', 'MD 8', 'ME 1', 'ME 2', 'MO 1', 'MO 2', 'MO 3', 'MO 4', 'MO 5', 'MO 6', 'MO 7', 'MO 8', 'MS 1', 'MS 2', 'MS 3', 'MS 4', 'NH 1', 'NH 2', 'NJ 1', 'NJ 2', 'NJ 3', 'NJ 4', 'NJ 5', 'NJ 6', 'NJ 7', 'NJ 8', 'NJ 9', 'NJ 10', 'NJ 11', 'NJ 12', 'OK 1', 'OK 2', 'OK 3', 'OK 4', 'OK 5', 'OR 1', 'OR 2', 'OR 3', 'OR 4', 'OR 5', 'PA 1', 'PA 2', 'PA 3', 'PA 4', 'PA 5', 'PA 6', 'PA 7', 'PA 8', 'PA 9', 'PA 10', 'PA 11', 'PA 12', 'PA 13', 'PA 14', 'PA 15', 'PA 16', 'PA 17', 'PA 18', 'RI 1', 'RI 2', 'TN 1', 'TN 2', 'TN 3', 'TN 4', 'TN 5', 'TN 6', 'TN 7', 'TN 8', 'TN 9']},
    {'time': 1352251800, 'districts': ['AR 1', 'AR 2', 'AR 3', 'AR 4']},
    # {'time': 1352253600, 'districts': ['AZ 1', 'AZ 2', 'AZ 3', 'AZ 4', 'AZ 5', 'AZ 6', 'AZ 7', 'AZ 8', 'AZ 9', 'CO 1', 'CO 2', 'CO 3', 'CO 4', 'CO 5', 'CO 6', 'CO 7', 'KS 1', 'KS 2', 'KS 3', 'KS 4', 'LA 1', 'LA 2', 'LA 3', 'LA 4', 'LA 5', 'LA 6', 'MI 1', 'MI 2', 'MI 3', 'MI 4', 'MI 5', 'MI 6', 'MI 7', 'MI 8', 'MI 9', 'MI 10', 'MI 11', 'MI 12', 'MI 13', 'MI 14', 'MN 1', 'MN 2', 'MN 3', 'MN 4', 'MN 5', 'MN 6', 'MN 7', 'MN 8', 'ND 1', 'NE 1', 'NE 2', 'NE 3', 'NM 1', 'NM 2', 'NM 3', 'NY 1', 'NY 2', 'NY 3', 'NY 4', 'NY 5', 'NY 6', 'NY 7', 'NY 8', 'NY 9', 'NY 10', 'NY 11', 'NY 12', 'NY 13', 'NY 14', 'NY 15', 'NY 16', 'NY 17', 'NY 18', 'NY 19', 'NY 20', 'NY 21', 'NY 22', 'NY 23', 'NY 24', 'NY 25', 'NY 26', 'NY 27', 'SD 1', 'TX 1', 'TX 2', 'TX 3', 'TX 4', 'TX 5', 'TX 6', 'TX 7', 'TX 8', 'TX 9', 'TX 10', 'TX 11', 'TX 12', 'TX 13', 'TX 14', 'TX 15', 'TX 16', 'TX 17', 'TX 18', 'TX 19', 'TX 20', 'TX 21', 'TX 22', 'TX 23', 'TX 24', 'TX 25', 'TX 26', 'TX 27', 'TX 28', 'TX 29', 'TX 30', 'TX 31', 'TX 32', 'TX 33', 'TX 34', 'TX 35', 'TX 36', 'WI 1', 'WI 2', 'WI 3', 'WI 4', 'WI 5', 'WI 6', 'WI 7', 'WI 8', 'WY 1']},
    {'time': 1352257200, 'districts': ['IA 1', 'IA 2', 'IA 3', 'IA 4', 'MT 1', 'NV 1', 'NV 2', 'NV 3', 'NV 4', 'UT 1', 'UT 2', 'UT 3', 'UT 4']},
    # {'time': 1352260800, 'districts': ['CA 1', 'CA 2', 'CA 3', 'CA 4', 'CA 5', 'CA 6', 'CA 7', 'CA 8', 'CA 9', 'CA 10', 'CA 11', 'CA 12', 'CA 13', 'CA 14', 'CA 15', 'CA 16', 'CA 17', 'CA 18', 'CA 19', 'CA 20', 'CA 21', 'CA 22', 'CA 23', 'CA 24', 'CA 25', 'CA 26', 'CA 27', 'CA 28', 'CA 29', 'CA 30', 'CA 31', 'CA 32', 'CA 33', 'CA 34', 'CA 35', 'CA 36', 'CA 37', 'CA 38', 'CA 39', 'CA 40', 'CA 41', 'CA 42', 'CA 43', 'CA 44', 'CA 45', 'CA 46', 'CA 47', 'CA 48', 'CA 49', 'CA 50', 'CA 51', 'CA 52', 'CA 53', 'HI 1', 'HI 2', 'ID 1', 'ID 2', 'WA 1', 'WA 2', 'WA 3', 'WA 4', 'WA 5', 'WA 6', 'WA 7', 'WA 8', 'WA 9', 'WA 10']},
    {'time': 1352264400, 'districts': ['AK 1']}
]

PRESIDENT_TIMES = [
    {'time': 1352246400, 'states': ['GA', 'IN', 'KY', 'SC', 'VA', 'VT']},
    {'time': 1352248200, 'states': ['NC', 'OH', 'WV']},
    {'time': 1352250000, 'states': ['AL', 'CT', 'DE', 'FL', 'IL', 'MA', 'MD', 'MO', 'MS', 'NH ''NJ', 'OK', 'OR', 'PA', 'RI', 'TN']},
    {'time': 1352251800, 'states': ['AR']},
    {'time': 1352253600, 'states': ['AZ', 'CO', 'KS', 'LA', 'MI', 'MN', 'ND', 'NE', 'NM', 'NY', 'TX', 'WI']},
    {'time': 1352257200, 'states': ['IA', 'MT 1', 'NV', 'UT']},
    {'time': 1352260800, 'states': ['CA', 'HI', 'ID', 'WA']},
    {'time': 1352264400, 'states': ['AK']}
]

# Constants for static media storage.
import os
if os.environ.get('DEPLOYMENT_TARGET', '') == 'production':
    S3_BUCKET = 'apps.npr.org'
    DEBUG = False
else:
    S3_BUCKET = 'stage-apps.npr.org'
    DEBUG = True
PRESIDENT_S3_KEY = '%s/states.csv' % PROJECT_NAME
PRESIDENT_FILENAME = 'www/states.csv'

HOUSE_S3_KEY = '%s/house.json' % PROJECT_NAME
HOUSE_FILENAME = 'www/house.json'

SENATE_S3_KEY = '%s/senate.json' % PROJECT_NAME
SENATE_FILENAME = 'www/senate.json'

STATIC_URL = 'http://%s/%s' % (S3_BUCKET, PROJECT_NAME)


# Constants for data imports.
STATE_FIELDS = [
    'is_test',
    'election_date',
    'state_postal',
    'county_number',
    'fips',
    'county_name',
    'race_number',
    'office_id',
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
CANDIDATE_FIELDS = [
    'candidate_number',
    'order',
    'party',
    'first_name',
    'middle_name',
    'last_name',
    'junior',
    'use_junior',
    'incumbent',
    'vote_count',
    'is_winner',
    'national_politician_id',
]
NUM_STATE_FIELDS = len(STATE_FIELDS)
NUM_CANDIDATE_FIELDS = len(CANDIDATE_FIELDS)
