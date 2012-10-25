#!/usr/bin/env python

import input as i
import output as o
import datetime

from fabric.api import *
from peewee import *
from models import Candidate, Race, State


"""
Base configuration
"""
env.project_name = 'electris'
env.deployed_name = 'swing-state-scorecard'
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
    Deploy the gzipped stuff to S3
    """
    local(('\
        s3cmd -P\
        --add-header=Content-encoding:gzip\
        --guess-mime-type\
        --recursive\
        --exclude states.csv\
        sync gzip/ s3://%(s3_bucket)s/%(project_name)s/') % env)


def _gzip_www():
    """
    Gzips everything in www and puts it all in gzip
    """
    o.gzip_www()


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
    run('cd %(repo_path)s; git fetch %(branch)s' % env)
    run('cd %(repo_path)s; git checkout %(branch)s; git pull origin %(branch)s' % env)


def install_requirements():
    run('%(virtualenv_path)s/bin/pip install -r %(repo_path)s/requirements.txt' % env)


def deploy():
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])
    _confirm_branch()
    _gzip_www()
    _deploy_to_s3()

    # checkout_latest()


def deploy_local_data():
    """
    Deploy the local data file to S3 (for electris pre-election.)
    """
    _gzip_www()
    local(('s3cmd -P --add-header=Content-encoding:gzip --guess-mime-type put gzip/states.csv s3://%(s3_bucket)s/%(deployed_name)s/') % env)
    local(('s3cmd -P --add-header=Content-encoding:gzip --guess-mime-type put gzip/js/combo_primer.js s3://%(s3_bucket)s/%(deployed_name)s/js/') % env)


def recreate_tables():
    """
    Private function to delete and recreate a blank database.
    """
    local('rm electris.db && touch electris.db')

    # Use the Peewee ORM to recreate tables.
    Candidate.create_table(fail_silently=True)
    Race.create_table(fail_silently=True)
    State.create_table(fail_silently=True)


def bootstrap_races():
    """
    Private function to load initial data for races.
    """
    local('rm electris.db && cp initial_data/electris_initial.db electris.db')


def update_polls():
    """
    Updates state predictions for presidential races against HuffPo's polling API.
    """
    i.update_polls()
    write_www_files()


def generate_initial_combos():
    o.generate_initial_combos()


def write_www_files():
    """
    Function to write output files to www from the database.
    This is probably going to be part of the cron routine on election night.
    """
    with settings(warn_only=True):
        local('rm www/states.csv')
        local('rm www/house.json')
        local('rm www/senate.json')
        local('rm www/president.json')
        local('rm www/js/combo_primer.js')

    o.write_president_csv()
    o.write_president_json()
    o.write_house_json()
    o.write_senate_json()
    o.generate_initial_combos()


def update_ap_data():
    """
    Gets actual AP data from the AP's top-of-ticket file.
    """
    data = i.get_ap_data()
    i.parse_ap_data(data)
    write_www_files()


def update_fake_ap_data():
    """
    Gets randomly assigned data from snapshot files in our timemachine.
    """
    data = i.get_fake_ap_data()
    i.parse_ap_data(data)
    write_www_files()


def wipe_status():
    """
    Blanks the status fields for congress and presidential races.
    """

    rq = Race.update(
        precincts_reporting=0,
        ap_called=False,
        ap_called_time=None,
        npr_called=False,
        npr_called_time=None
    )
    rq.execute()

    cq = Candidate.update(
        vote_count=0,
        ap_winner=False,
        npr_winner=False
    )
    cq.execute()

    sq = State.update(
        ap_call='u',
        ap_called_at=None,
        npr_call='u',
        npr_called_at=None,
        precincts_reporting=0,
        rep_vote_count=0,
        dem_vote_count=0
    )
    sq.execute()
    write_www_files()


def local_reset():
    """
    Resets the local environment to a fresh copy of the db and data.
    """
    bootstrap_races()
    write_www_files()


def save_ap_data():
    minute = datetime.datetime.now().minute
    hour = datetime.datetime.now().hour
    with open('test_data/timemachine/US_%s-%s.txt' % (hour, minute), 'w') as f:
        data = ''
        for line in i.get_ap_data():
            data += line
        f.write(data)


def shiva_the_destroyer():
    """
    Deletes the app from s3
    """
    with settings(warn_only=True):
        local('s3cmd del --recursive s3://%(s3_bucket)s/%(deployed_name)s' % env)
        run('rm -rf %(path)s')
