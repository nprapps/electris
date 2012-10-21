#!/usr/bin/env python

import input as i
import output as o

from pollster import Pollster
from fabric.api import *
from peewee import *
from models import Candidate, Race, State


"""
Base configuration
"""
env.project_name = 'electris'
env.user = 'ubuntu'
env.python = 'python2.7'
env.path = '/home/ubuntu/apps/%(project_name)s' % env
env.repo_path = '%(path)s/repository' % env
env.virtualenv_path = '%(path)s/virtualenv' % env
env.forward_agent = True


"""
Environments
"""
def production():
    env.settings = 'production'
    env.s3_bucket = 'apps.npr.org'
    env.hosts = ['54.245.114.14']


def staging():
    env.settings = 'staging'
    env.s3_bucket = 'stage-apps.npr.org'
    env.hosts = ['50.112.92.131']


"""
Branches
"""
def stable():
    """
    Work on stable branch.
    """
    env.branch = 'stable'


def master():
    """
    Work on development branch.
    """
    env.branch = 'master'


def branch(branch_name):
    """
    Work on any specified branch.
    """
    env.branch = branch_name


"""
Commands
"""
def _confirm_branch():
    if (env.settings == 'production' and env.branch != 'stable'):
        answer = prompt("You are trying to deploy the '%(branch)s' branch to production.\nYou should really only deploy a stable branch.\nDo you know what you're doing?" % env, default="Not at all")
        if answer not in ('y', 'Y', 'yes', 'Yes', 'buzz off', 'screw you'):
            exit()


def _deploy_to_s3():
    """
    Deploy the gzipped stuff to
    """
    local(('s3cmd -P --add-header=Content-encoding:gzip --guess-mime-type --recursive --exclude states.csv sync gzip/ s3://%(s3_bucket)s/%(project_name)s/') % env)


def _gzip_www():
    """
    Gzips everything in www and puts it all in gzip
    """
    local('python gzip_www.py')


def setup():
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])

    setup_directories()
    setup_virtualenv()
    clone_repo()
    checkout_latest()
    install_requirements()


def setup_directories():
    run('mkdir -p %(path)s' % env)


def setup_virtualenv():
    run('virtualenv -p %(python)s --no-site-packages %(virtualenv_path)s' % env)
    run('source %(virtualenv_path)s/bin/activate' % env)


def clone_repo():
    run('git clone git@github.com:nprapps/%(project_name)s.git %(repo_path)s' % env)


def checkout_latest():
    run('cd %(repo_path)s; git checkout %(branch)s; git pull origin %(branch)s' % env)


def install_requirements():
    run('%(virtualenv_path)s/bin/pip install -r %(repo_path)s/requirements.txt' % env)


def deploy():
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])
    _confirm_branch()
    _gzip_www()
    _deploy_to_s3()

    checkout_latest()


def _recreate_tables():
    """
    Private function to delete and recreate a blank database.
    """
    local('rm electris.db && touch electris.db')

    # Use the Peewee ORM to recreate tables.
    Candidate.create_table(fail_silently=True)
    Race.create_table(fail_silently=True)
    State.create_table(fail_silently=True)


def _bootstrap_races():
    """
    Private function to load initial data for races.
    """
    _recreate_tables()

    i.bootstrap_president()

    # Right now, bootstrapping the house races involves a call to AP.
    # Should change this.
    data = i.get_ap_data()
    i.parse_ap_data(data)

    # With appropriate bootstrapping data, this step is unnecessary.
    i.bootstrap_house_times()
    i.bootstrap_senate_times()


def write_www_files():
    """
    Private function to write output files for www from the database.
    This is probably going to be part of the cron routine on election night.
    """
    with settings(warn_only=True):
        local('rm www/states.csv')
        local('rm www/house.json')
        local('rm www/senate.json')
        local('rm www/president.json')

    o.write_president_csv()
    o.write_president_json()
    o.write_house_json()
    o.write_senate_json()


def update_ap_data():
    data = i.get_ap_data()
    i.parse_ap_data(data)
    write_www_files()


def local_reset():
    """
    Resets the local environment to a fresh copy of the db and data.
    """
    _bootstrap_races()
    write_www_files()


def load_test_db():
    """
    Copies a snapshot of the electris DB with settings as defined in
    test_data/bigboard/README.md and regenerates output files for www.
    """
    local('rm electris.db')
    local('cp test_data/bigboard/electris_test.db electris.db')
    write_www_files()


def update_polls():
    """
    Updates state predictions for presidential races against HuffPo's polling API.
    """
    pollster = Pollster()

    for state in State.select().where(State.electoral_votes > 1):
        charts = pollster.charts(topic='2012-president', state=state.id)

        if charts:
            chart = charts[0]
        else:
            print 'NO DATA FOR %s' % state.id.upper()
            continue

        obama = 0
        romney = 0

        if chart.estimates:
            for estimate in chart.estimates:
                if estimate['choice'] == "Obama":
                    obama = estimate['value']
                elif estimate['choice'] == "Romney":
                    romney = estimate['value']
        else:
            print 'NO ESTIMATES FOR %s' % state.id.upper()
            continue

        prediction = "t"

        if abs(obama - romney) > 15:
            if obama > romney:
                prediction = "sd"
            else:
                prediction = "sr"
        elif abs(obama - romney) > 7.5:
            if obama > romney:
                prediction = "ld"
            else:
                prediction = "lr"

        uq = State.update(prediction=prediction).where(State.id == state)
        uq.execute()

    write_www_files()


def shiva_the_destroyer():
    """
    Deletes the app from s3
    """
    with settings(warn_only=True):
        local('s3cmd del --recursive s3://%(s3_bucket)s/%(project_name)s' % env)
        run('rm -rf %(path)s')
