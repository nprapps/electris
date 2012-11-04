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
    accept_ap_call = BooleanField(default=True)
    poll_closing_time = DateTimeField(null=True)
    featured_race = BooleanField(default=False)
    prediction = CharField(null=True)
    total_precincts = IntegerField(null=True)
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

    # Status
    precincts_reporting = IntegerField(null=True)
    ap_called = BooleanField(default=False)
    ap_called_time = DateTimeField(null=True)
    npr_called = BooleanField(default=False)
    npr_called_time = DateTimeField(null=True)

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

    @property
    def flipped(self):
        """
        Returns a two-tuple; winning party, losing party.
        """
        def _format_output(candidate):
            if candidate == 'r':
                return 'republicans'
            elif candidate == 'd':
                return 'democrats'
            elif candidate == 'o':
                return 'other'

        if self.winner and self.prediction:
            return (_format_output(self.winner), _format_output(self.prediction))

        return (None, None)

    @property
    def has_flipped(self):
        """
        Check to see if the winner matches the predicted winner.
        """
        if self.called == True:

            # If the race is called -- return!
            if unicode(self.winner) == unicode(self.prediction):

                # If the winner is predicted, return false.
                return False
            else:

                # Otherwise, YES!
                return True

        # If'n this race hasn't been called, return false.
        return False

    @property
    def winner(self):
        for candidate in Candidate.select().where(Candidate.race == self):
            if self.accept_ap_call == True:
                if candidate.ap_winner == True:
                    if candidate.party == 'GOP':
                        return 'r'
                    elif candidate.party == 'Dem':
                        return 'd'
                    else:
                        return 'o'
            else:
                if candidate.npr_winner == True:
                    if candidate.party == 'GOP':
                        return 'r'
                    elif candidate.party == 'Dem':
                        return 'd'
                    else:
                        return 'o'
        return None

    @property
    def called(self):
        if self.accept_ap_call == True:
            return self.ap_called

        else:
            return self.npr_called

        return False

    def has_incumbents(self):
        for candidate in Candidate.select().where(Candidate.race == self):
            if candidate.incumbent == True:
                return True

        return False

    def total_votes(self):
        count = 0
        for c in Candidate.select().where(Candidate.race == self):
            count += c.vote_count
        return count

    def percent_reporting(self):
        try:
            getcontext().prec = 2
            percent = Decimal(self.precincts_reporting) / Decimal(self.total_precincts)
            return round(float(percent) * 100, 0)
        except InvalidOperation:
            return 0.0


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
    race = ForeignKeyField(Race, null=True)
    candidate_number = CharField()
    ballot_order = CharField()
    use_junior = CharField()

    # Status
    vote_count = IntegerField(default=False)
    ap_winner = BooleanField(default=False)
    npr_winner = BooleanField(default=False)

    class Meta:
        """
        Uses house_senate_candidates table but changes/adds columns.
        """
        db_table = 'house_senate_candidates'
        database = database

    def __unicode__(self):
        return u'%s %s (%s)' % (self.first_name, self.last_name, self.party)

    def vote_percent(self):
        try:
            getcontext().prec = 2
            percent = Decimal(self.vote_count) / Decimal(self.race.total_votes())
            return round(float(percent) * 100, 0)
        except InvalidOperation:
            return 0.0


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
    accept_ap_call = BooleanField(default=True)
    total_precincts = IntegerField(null=True)

    # Status.
    ap_call = CharField(max_length=255)
    ap_called_at = CharField(max_length=255, null=True)
    npr_call = CharField(max_length=255)
    npr_called_at = CharField(max_length=255, null=True)
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

    @property
    def winner(self):
        if self.accept_ap_call == True:
            if self.ap_call != 'u':
                return self.ap_call
        else:
            if self.npr_call != 'u':
                return self.npr_call

        return None

    @property
    def called(self):
        if self.accept_ap_call == True:
            if self.ap_call != 'u':
                return True
        else:
            if self.npr_call != 'u':
                return True

        return False

    def percent_reporting(self):
        try:
            getcontext().prec = 2
            percent = Decimal(self.precincts_reporting) / Decimal(self.total_precincts)
            return round(float(percent) * 100, 0)
        except InvalidOperation:
            return 0.0

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
            percent = Decimal(self.rep_vote_count) / Decimal(self.dem_vote_count + self.rep_vote_count)
            return round(float(percent) * 100, 1)
        else:
            return 0

    def dem_vote_percent(self):
        if self.dem_vote_count > 0:
            getcontext().prec = 3
            percent = Decimal(self.dem_vote_count) / Decimal(self.dem_vote_count + self.rep_vote_count)
            return round(float(percent) * 100, 1)
        else:
            return 0
