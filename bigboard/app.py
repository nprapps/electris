#!/usr/bin/env python

from flask import Flask
from flask import render_template

from peewee import *
from flask_peewee.db import Database
from flask_peewee.utils import get_object_or_404
from flask_peewee.rest import RestAPI

from bigboard.models import Race, Candidate

DATABASE = {
    'name': 'house_senate.db',
    'engine': 'peewee.SqliteDatabase',
    'check_same_thread': False,
}
DEBUG = True
SECRET_KEY = 'sad;jsad;jasd98f823123'

app = Flask(__name__)
app.config.from_object(__name__)

database = Database(app)

class Race(database.Model):
	id = PrimaryKeyField(primary_key=True)
	state = CharField()
	state_short = CharField()
	district = IntegerField()
	race_type = CharField(choices=(('h', 'U.S. House'), ('s', 'U.S. Senate')))
	ap_called = BooleanField(default=False)
	ap_called_time = DateTimeField(null=True, blank=True)
	npr_called = BooleanField(default=False)
	npr_called_time = DateTimeField(null=True, blank=True)

	def __unicode__(self):
		if self.race_type == "h":
			return u'%s %s %s' % (self.race_type, self.state_short, self.district)
		else:
			return u'%s %s' % (self.race_type, self.state_short)


class Candidate(database.Model):
	id = PrimaryKeyField(primary_key=True)
	race = ForeignKeyField(Race, null=True, blank=True)
	first_name = CharField()
	last_name = CharField()
	middle_name = CharField(null=True, blank=True)
	junior = CharField(null=True, blank=True)
	use_junior = BooleanField(default=False)
	incumbent = BooleanField(default=False)
	current_vote_count = IntegerField(null=True, blank=True)
	is_winner = BooleanField(default=False)

	def __unicode__(self):
		return u'%s: %s %s' % (self.race, self.first_name, self.last_name)

@app.route('/races/')
def race_list():
    races = Race.select().order_by(Race.state, Race.district)
    context = {
        'races': races
    }
    return render_template('race_list.html', **context)

@app.route('/races/<state_short>/<district>/')
def race_detail(state_short, district):
    race = get_object_or_404(Race, state_short=state_short, district=district)
    candidates = Candidate.filter(race=race)
    context = {
        'race': race,
        'candidates': candidates
    }
    return render_template('race_detail.html', **context)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
