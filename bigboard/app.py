#!/usr/bin/env python

from flask import Flask
from flask import render_template

# Peewee for the models and ORM.
# Flask-Peewee for the utilities.
from peewee import *
from flask_peewee.db import Database
from flask_peewee.utils import get_object_or_404

# Set up the connections for the DB.
# You'd know these as "settings."
DATABASE = {
    'name': 'house_senate.db',
    'engine': 'peewee.SqliteDatabase',
    'check_same_thread': False,
}
DEBUG = True
SECRET_KEY = 'sad;jsad;jasd98f823123'

# Instantiate the application.
app = Flask(__name__)
app.config.from_object(__name__)

# Connect to the DB layer.
database = Database(app)

# Set up the models.
class Race(database.Model):
	"""
	Represents a single race in a single district for a single side of our bicameral congress.
	Does not: Have a concept of a year.
	Still needs: A last-updated field.
	"""
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
	"""
	Represents a single candidate in a single race.
	Does not: Have a relationship to more than one race.
	Still needs: A last-updated field.
	"""
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


# Views! Remember these?
@app.route('/races/')
def race_list():
	"""
	All of the races we're tracking.
	Eventually, these will need to be ordered more interestingly.
	"""
    races = Race.select().order_by(Race.state, Race.district)
    context = {
        'races': races
    }
    return render_template('race_list.html', **context)

@app.route('/races/<state_short>/<district>/')
def race_detail(state_short, district):
	"""
	A single race with all of the associated candidates.
	"""
    race = get_object_or_404(Race, state_short=state_short, district=district)
    candidates = Candidate.filter(race=race)
    context = {
        'race': race,
        'candidates': candidates
    }
    return render_template('race_detail.html', **context)

# Shenanigans. This ties the app to a port and executes it.
if __name__ == "__main__":
    app.run(host='0.0.0.0')
