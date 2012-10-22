import re
from decimal import *
from peewee import *
import cms_settings as settings

database = SqliteDatabase(settings.DATABASE_FILENAME, check_same_thread=False)


def intcomma(value):
    """
    Converts an integer to a string containing commas every three digits.
    For example, 3000 becomes '3,000' and 45000 becomes '45,000'.
    Shamelessly ripped off from django.contrib.humanize.
    And, hey: Recursive!
    """
    orig = str(value)
    new = re.sub("^(-?\d+)(\d{3})", '\g<1>,\g<2>', orig)
    if orig == new:
        return new
    else:
        return intcomma(new)


class Race(Model):
    """
    Normalizes the race-level data back into a race model.
    """

    rowid = PrimaryKeyField()
    slug = CharField(max_length=255)
    state_postal = CharField(max_length=255)
    state_name = CharField(max_length=255)
    office_code = CharField(max_length=255)
    office_name = CharField(max_length=255)
    district_id = IntegerField()
    district_name = CharField(max_length=255, null=True)
    precincts_reporting = IntegerField(null=True)
    total_precincts = IntegerField(null=True)
    accept_ap_call = BooleanField(default=False)
    ap_called = BooleanField(default=False)
    ap_called_time = DateTimeField(null=True)
    npr_called = BooleanField(default=False)
    npr_called_time = DateTimeField(null=True)
    poll_closing_time = DateTimeField(null=True)

    # Imported but not used.
    is_test = CharField(null=True)
    election_date = CharField(null=True)
    county_number = CharField(null=True)
    fips = CharField(null=True)
    county_name = CharField(null=True)
    race_number = CharField(null=True)
    race_type_id = CharField(null=True)
    seat_name = CharField(null=True)
    race_type_party = CharField(null=True)
    race_type = CharField(null=True)
    office_description = CharField(null=True)
    number_of_winners = CharField(null=True)
    number_in_runoff = CharField(null=True)

    class Meta:
        """
        Creates a new 'races' table.
        """
        db_table = 'races'
        database = database

    def __unicode__(self):
        return u'%s: %s-%s' % (
            self.office_name,
            self.state_postal,
            self.district_id)


class Candidate(Model):
    """
    Normalizes the candidate data into a candidate model.
    """
    rowid = PrimaryKeyField()
    npid = IntegerField()
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    middle_name = CharField(max_length=255)
    junior = CharField(max_length=255, null=True)
    incumbent = BooleanField(default=False)
    party = CharField(max_length=255)
    vote_count = IntegerField(default=False)
    ap_winner = BooleanField(default=False)
    npr_winner = BooleanField(default=False)

    # Relationship to a race.
    race = ForeignKeyField(Race, null=True)

    # Imported from AP but unused.
    candidate_number = CharField()
    ballot_order = CharField()
    use_junior = CharField()

    class Meta:
        """
        Uses house_senate_candidates table but changes/adds columns.
        """
        db_table = 'house_senate_candidates'
        database = database

    def __unicode__(self):
        return u'%s %s (%s)' % (self.first_name, self.last_name, self.party)


class State(Model):
    """
    Access to the states table via model ORM.
    """
    rowid = PrimaryKeyField()
    id = CharField(max_length=255)
    stateface = CharField(max_length=255)
    name = CharField(max_length=255)
    abbr = CharField(max_length=255)
    electoral_votes = IntegerField()
    polls_close = CharField(max_length=255)
    prediction = CharField(max_length=255, null=True)
    ap_call = CharField(max_length=255)
    ap_called_at = CharField(max_length=255, null=True)
    accept_ap_call = BooleanField(default=True)
    npr_call = CharField(max_length=255)
    npr_called_at = CharField(max_length=255, null=True)
    total_precincts = IntegerField(null=True)
    precincts_reporting = IntegerField(null=True)
    rep_vote_count = IntegerField(null=True)
    dem_vote_count = IntegerField(null=True)

    class Meta:
        """
        Uses the existing states table. Does not change columns.
        """
        db_table = 'states'
        database = database

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.electoral_votes)

    def human_rep_vote_count(self):
        if self.rep_vote_count > 0:
            return intcomma(self.rep_vote_count)
        else:
            return 0

    def human_dem_vote_count(self):
        if self.dem_vote_count > 0:
            return intcomma(self.dem_vote_count)
        else:
            return 0

    def rep_vote_percent(self):
        if self.rep_vote_count > 0:
            getcontext().prec = 3
            return str(Decimal(self.rep_vote_count) / Decimal(self.dem_vote_count + self.rep_vote_count) * 100)
        else:
            return 0

    def dem_vote_percent(self):
        if self.dem_vote_count > 0:
            getcontext().prec = 3
            return str(Decimal(self.dem_vote_count) / Decimal(self.dem_vote_count + self.rep_vote_count) * 100)
        else:
            return 0
