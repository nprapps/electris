#!/usr/bin/env python

from datetime import datetime
import json
import re

from flask import Flask
from flask import render_template, request
import pytz
from operator import itemgetter

import cms_settings as settings
from util import get_database, get_states, regenerate_president, push_results_to_s3, get_house_senate

app = Flask(__name__)


@app.route('/races/<house>/', methods=['GET', 'POST'])
def house(house):
    """
    Read/update list of house candidates.
    """

    # Make the database connection.
    db = get_database()

    # Establish which house of congress this is.
    # Translate it to AP's uppercase single-letter version.
    house_slug = 'H'
    if house == 'senate':
        house_slug = 'S'

    # If we're just looking ... return stuff to a template.
    if request.method == 'GET':

        # Run a query against the db we have.
        # This query is from utils -- it gets all of the house/senate members.
        query = get_house_senate(db)

        # Set up a list. Need to get only certain people.
        candidates = []

        # Loop through the query.
        for candidate in query:

            # Get only the matching house of congress.
            if candidate['office_code'] == house_slug.upper():

                # Get only Democrats or Republicans.
                # There's an exception for Angus Young.
                if candidate['party'] in ['Dem', 'GOP']:

                    # Append the lucky winners to the candidate list.
                    candidates.append(candidate)

        # Return stuff to the page.
        context = {

            # Return settings for some reason.
            'settings': settings,

            # Return the candidate list, sorted by race_slug, then state, then district.
            'candidates': sorted(candidates, key=itemgetter(21, 0, 3)),

            # Return the house of congress.
            'house': house
        }

        # Render to the template and unpack the context dictionary for Jinja2.
        return render_template('house_senate.html', **context)

    # Alternately, what if someone is POSTing?
    if request.method == 'POST':

        # First, try and get the race.
        race_slug = request.form.get('race_slug', None)

        # Build the matching DB representation, e.g., ak 1 instead of ak1.
        race_slug = re.split('(\d+)', race_slug)
        race_slug = '%s %s' % (race_slug[0], race_slug[1])

        # Next, try to get the AP call.
        accept_ap_call = request.form.get('accept_ap_call', None)
        if accept_ap_call:

            # Figure out which direction we're going and send an appropriate message.
            if accept_ap_call.lower() == 'true':
                accept_ap_call = "1"
                message = "Accepting AP calls on %s" % race_slug.upper()
            else:
                accept_ap_call = "0"
                message = "Will <strong>not</strong> accept AP calls on %s" % race_slug.upper()

        # If all the pieces are here, do something.
        if race_slug != None and accept_ap_call != None:

            # Run some SQL to change the status of this set of candidate's accept_ap_call column.
            db.execute('UPDATE house_senate_candidates SET accept_ap_call="%s" WHERE race_slug="%s"' % (
                accept_ap_call,
                race_slug))

            # Commit!
            db.commit()

        # Return the message instead of a template.
        return "%s|%s" % (race_slug.upper(), message)


@app.route('/', methods=['GET', 'POST'])
def president():
    """
    Read/update list of presidential state winners.
    """
    db = get_database()
    states = get_states(db)

    if request.method == 'POST':
        for state in states:
            prediction = request.form.get('prediction-%s' % state['id'], '')
            accept_ap_call = 'y' if request.form.get('accept-ap-call-%s' % state['id'], '') == 'on' else 'n'
            npr_call = request.form.get('npr-%s' % state['id'], '')
            npr_called_at = state['npr_called_at']

            # If NPR call updated, save time of change
            if npr_call != state['npr_call']:
                npr_called_at = datetime.now(tz=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S %z');

            db.execute('UPDATE states SET prediction=?, accept_ap_call=?, npr_call=?, npr_called_at=? WHERE id=?', (prediction, accept_ap_call, npr_call, npr_called_at, state['id']))

        db.commit()

        states = get_states(db)

        # When deployed, the CMS does not update the data files to prevent bad interactions with the AP cron job.
        if settings.DEBUG:
            regenerate_president(states)
            push_results_to_s3()

    db.close()

    context = {
        'settings': settings,
        'states': states
    }

    return render_template('winners.html', **context)

@app.route('/data', methods=['GET', 'POST'])
def data():
    db = get_database()
    states = get_states(db)

    return json.dumps([dict(zip(s.keys(), s)) for s in states])

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=settings.DEBUG)
