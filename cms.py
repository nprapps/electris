#!/usr/bin/env python

from flask import Flask
from flask import render_template, request

import cms_settings as settings
from models import Race, Candidate, State

app = Flask(__name__)


@app.route('/races/president/', methods=['GET', 'POST'])
def president():
    """
    Read/update list of presidential state winners.
    """
    if request.method == 'GET':

        states = State.select().where(State.electoral_votes > 1)

        context = {
            'states': states,
            'settings': settings
        }

        return render_template('president.html', **context)

    if request.method == 'POST':

        # First, try and get the state.
        race_slug = request.form.get('race_slug', None)

        # Next, try to get the AP call.
        accept_ap_call = request.form.get('accept_ap_call', None)
        if accept_ap_call:

            # Figure out which direction we're going and send an appropriate message.
            if accept_ap_call.lower() == 'true':
                accept_ap_call = True
            else:
                accept_ap_call = False

        # If all the pieces are here, do something.
        if race_slug != None and accept_ap_call != None:

            # Run some SQL to change the status of this set of candidate's accept_ap_call column.
            sq = State.update(accept_ap_call=accept_ap_call).where(State.id == race_slug)
            sq.execute()

            # Clear the NPR winner status of candidates who we accept AP calls for.
            if accept_ap_call == False:

                uq = State.update(npr_call='n').where(State.id == race_slug)
                uq.execute()

        # Try and get the winner.
        party = request.form.get('party', None)

        # Try and get a clear_all.
        clear_all = request.form.get('clear_all', None)

        if race_slug != None and clear_all != None:

            # If we're passing clear_all as true ...
            if clear_all == 'true':

                # Clear the NPR winner status of all of the candidates.
                uq = State.update(npr_call='n').where(State.id == race_slug)
                uq.execute()

        # If all of the pieces are here, do something.
        if race_slug != None and party != None:

            uq = State.update(npr_call="%s" % party).where(State.id == race_slug)
            print uq.execute()

        # Return the message instead of a template.
        return ""


@app.route('/races/<house>/', methods=['GET', 'POST'])
def house(house):
    """
    Read/update list of house candidates.
    """

    house_slug = u'H'
    if house == 'senate':
        house_slug = u'S'

    if request.method == 'GET':

        # Get all of the candidates that match this race which are either
        # Republicans or Democrats or have the first name Angus.
        candidates = Candidate\
            .select()\
            .join(Race)\
            .where(
                Race.office_code == house_slug,
                (Candidate.party == 'Dem') | (Candidate.party == 'GOP') | (Candidate.first_name == 'Angus'),
                Candidate.last_name != 'Dill')\
            .order_by(
                Race.state_postal.desc(),
                Race.district_id.asc(),
                Candidate.party.asc())

        context = {
            'settings': settings,
            'candidates': candidates,
            'house': house
        }

        return render_template('house_senate.html', **context)

    # Alternately, what if someone is POSTing?
    if request.method == 'POST':

        # First, try and get the race.
        race_slug = request.form.get('race_slug', None)
        race = Race.select().where(Race.slug == race_slug).get()

        # Next, try to get the AP call.
        accept_ap_call = request.form.get('accept_ap_call', None)
        if accept_ap_call:

            # Figure out which direction we're going and send an appropriate message.
            if accept_ap_call.lower() == 'true':
                accept_ap_call = True
            else:
                accept_ap_call = False

        # If all the pieces are here, do something.
        if race_slug != None and accept_ap_call != None:

            # Run some SQL to change the status of this set of candidate's accept_ap_call column.
            race.accept_ap_call = accept_ap_call
            race.save()

            # Clear the NPR winner status of candidates who we accept AP calls for.
            if accept_ap_call == False:
                rq = Candidate.update(npr_winner=False).where(Candidate.race == race)
                rq.execute()

        # Try and get the winner.
        first_name = request.form.get('first_name', None)
        last_name = request.form.get('last_name', None)

        # Try and get a clear_all.
        clear_all = request.form.get('clear_all', None)

        if race_slug != None and clear_all != None:

            # If we're passing clear_all as true ...
            if clear_all == 'true':

                # Clear the NPR winner status of all of the candidates.
                rq = Candidate.update(npr_winner=False).where(Candidate.race == race)
                rq.execute()

        # If all of the pieces are here, do something.
        if race_slug != None and first_name != None and last_name != None:

            # First, clear the NPR winner status of all of the other candidates.
            rq = Candidate.update(npr_winner=False).where(Candidate.race == race)
            rq.execute()

            # Next, set one person as the winner.
            candidate = Candidate.select().where(
                Candidate.race == race,
                Candidate.first_name == first_name,
                Candidate.last_name == last_name
            ).get()
            candidate.npr_winner = True
            candidate.save()

        # Return the message instead of a template.
        return ""


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=settings.DEBUG)
