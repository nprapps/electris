#!/usr/bin/env python

import datetime
import json
from time import sleep

import boto
from boto.s3.key import Key
from fabric.api import *
from peewee import *
from tumblr import Api

import input as i
from models import Candidate, Race, State
import output as o

"""
Base configuration
"""
env.project_name = 'electris'
env.deployed_name = 'live-results-election-2012'
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
    env.alt_s3_bucket = 'apps2.npr.org'
    env.hosts = ['cron.nprapps.org']


def staging():
    env.settings = 'staging'
    env.s3_bucket = 'stage-apps.npr.org'
    env.alt_s3_bucket = None
    env.hosts = ['cron-staging.nprapps.org']


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
        --add-header=Cache-control:max-age=5\
        --add-header=Content-encoding:gzip\
        --guess-mime-type\
        --recursive\
        --exclude *.json\
        sync gzip/ s3://%(s3_bucket)s/%(deployed_name)s/') % env)
    if env.alt_s3_bucket:
        local(('\
            s3cmd -P\
            --add-header=Cache-control:max-age=5\
            --add-header=Content-encoding:gzip\
            --guess-mime-type\
            --recursive\
            --exclude *.json\
           sync  gzip/ s3://%(alt_s3_bucket)s/%(deployed_name)s/') % env)


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
    require('settings', provided_by=[production, staging])

    run('mkdir -p %(path)s' % env)


def setup_virtualenv():
    require('settings', provided_by=[production, staging])

    run('virtualenv -p %(python)s --no-site-packages %(virtualenv_path)s' % env)
    run('source %(virtualenv_path)s/bin/activate' % env)


def clone_repo():
    require('settings', provided_by=[production, staging])

    run('git clone git@github.com:nprapps/%(project_name)s.git %(repo_path)s' % env)


def checkout_latest():
    require('settings', provided_by=[production, staging])

    run('cd %(repo_path)s; git fetch' % env)
    run('cd %(repo_path)s; git checkout %(branch)s; git pull origin %(branch)s' % env)


def install_requirements():
    require('settings', provided_by=[production, staging])

    run('%(virtualenv_path)s/bin/pip install -r %(repo_path)s/requirements.txt' % env)


def deploy():
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])
    _confirm_branch()
    _gzip_www()
    _deploy_to_s3()

    with settings(warn_only=True):
            sudo('service electris_cms stop')
            sudo('service electris_cron stop')

    checkout_latest()

    sudo('service electris_cms start')
    sudo('service electris_cron start')

def deploy_local_data():
    """
    Deploy the local data files to S3.
    """
    write_www_files()
    _gzip_www()
    local(('s3cmd -P --add-header=Cache-control:max-age=5 --add-header=Content-encoding:gzip --guess-mime-type put gzip/*.json s3://%(s3_bucket)s/%(deployed_name)s/') % env)
    if env.alt_s3_bucket:
        local(('s3cmd -P --add-header=Cache-control:max-age=5 --add-header=Content-encoding:gzip --guess-mime-type put gzip/*.json s3://%(alt_s3_bucket)s/%(deployed_name)s/') % env)


def deployment_cron():
    """
    Deploy new data to S3 faster than we can with cron.
    """
    while True:
        deploy_local_data()
        sleep(5)


def backup_electris_db():
    """
    Backup the running electris database to S3.
    """
    local(('s3cmd -P  --add-header=Cache-control:max-age=5 --guess-mime-type put electris.db s3://%(s3_bucket)s/%(deployed_name)s/') % env)
    if env.alt_s3_bucket:
        local(('s3cmd -P  --add-header=Cache-control:max-age=5 --guess-mime-type put electris.db s3://%(alt_s3_bucket)s/%(deployed_name)s/') % env)


def recreate_tables():
    """
    Private function to delete and recreate a blank database.
    """
    with settings(warn_only=True):
        local('rm electris.db')
        local('&& touch electris.db')

    # Use the Peewee ORM to recreate tables.
    Candidate.create_table(fail_silently=True)
    Race.create_table(fail_silently=True)
    State.create_table(fail_silently=True)


def bootstrap_races():
    """
    Private function to load initial data for races.
    """
    with settings(warn_only=True):
        local('rm electris.db')
        local('cp initial_data/electris_initial.db electris.db')


def update_backchannel():
    """
    Update data for the backchannel from Tumblr
    """
    TUMBLR_FILENAME = 'www/tumblr.json'
    TUMBLR_BLOG_ID = 'nprbackchannel'
    TUMBLR_MAX_POSTS = 10

    api = Api(TUMBLR_BLOG_ID)

    posts = list(api.read(max=TUMBLR_MAX_POSTS))

    posts.reverse()

    with open(TUMBLR_FILENAME, 'w') as f:
        f.write(json.dumps(posts))

    if 'settings' in env:
        conn = boto.connect_s3()
        bucket = conn.get_bucket(env.s3_bucket)
        key = Key(bucket)
        key.key = '/'.join([env.deployed_name, TUMBLR_FILENAME])
        key.set_contents_from_filename(
            TUMBLR_FILENAME,
            policy='public-read',
            headers={'Cache-Control': 'max-age=5 no-cache no-store must-revalidate'}
        )
        if env.alt_s3.bucket:
            conn = boto.connect_s3()
            bucket = conn.get_bucket(env.alt_s3_bucket)
            key = Key(bucket)
            key.key = '/'.join([env.deployed_name, TUMBLR_FILENAME])
            key.set_contents_from_filename(
                TUMBLR_FILENAME,
                policy='public-read',
                headers={'Cache-Control': 'max-age=5 no-cache no-store must-revalidate'}
            )


def write_www_files():
    """
    Function to write output files to www from the database.
    This is probably going to be part of the cron routine on election night.
    """
    with settings(warn_only=True):
        local('rm www/states.json')
        local('rm www/house.json')
        local('rm www/senate.json')
        local('rm www/president.json')
        local('rm www/bop.json')
        local('rm www/bop_jsonp.json')

    o.write_electris_json()
    o.write_president_json()
    o.write_house_json()
    o.write_senate_json()
    o.write_bop_json()


def update_ap_data():
    """
    Gets actual AP data from the AP's top-of-ticket file.
    """
    data = i.get_ap_data()
    ne_data = i.get_ap_district_data('NE')
    me_data = i.get_ap_district_data('ME')

    i.parse_ap_data(data, ne_data, me_data)


def update_fake_ap_data():
    """
    Gets randomly assigned data from snapshot files in our timemachine.
    """
    data = i.get_fake_ap_data()
    ne_data = i.get_fake_ap_district_data('NE')
    me_data = i.get_fake_ap_district_data('ME')

    i.parse_ap_data(data, ne_data, me_data)
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


def reset():
    """
    Reset the environment on the server with a fresh copy of the database.
    """
    require('settings', provided_by=[production, staging])

    with settings(warn_only=True):
        sudo('service electris_cms stop')
        sudo('service electris_cron stop')

    with cd(env.repo_path):
        run('rm electris.db')
        run('cp initial_data/electris_initial.db electris.db')
        write_www_files()
        sudo('service electris_cms start')
        sudo('service electris_cron start')


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

    for state_code in ['NE', 'ME']:
        try:
            with open('test_data/timemachine/%s_D_%s-%s.txt' % (state_code, hour, minute), 'w') as f:
                data = ''
                for line in i.get_ap_district_data(state_code):
                    data += line
                f.write(data)
        except:
            pass


def deploy_audio(filename):
    """
    Deploys an audio status file to status.json
    """
    require('settings', provided_by=[production, staging])
    local('s3cmd -P --add-header=Cache-control:max-age=5 put initial_data/' + filename + ' s3://%(s3_bucket)s/%(deployed_name)s/status.json' % env)
    if env.alt_s3_bucket:
        local('s3cmd -P --add-header=Cache-control:max-age=5 put initial_data/' + filename + ' s3://%(alt_s3_bucket)s/%(deployed_name)s/status.json' % env)


def audio_off():
    """
    Shortcut to deploy_audio:status-off.json
    """
    deploy_audio('status-off.json')


def audio_pregame():
    """
    Shortcut to deploy_audio:status-pregame.json
    """
    deploy_audio('status-pregame.json')


def audio_live():
    """
    Shortcut to deploy_audio:status-live.json
    """
    deploy_audio('status-live.json')


def shiva_the_destroyer():
    """
    Deletes the app from s3
    """
    with settings(warn_only=True):
        local('s3cmd del --recursive s3://%(s3_bucket)s/%(deployed_name)s' % env)
        if env.alt_s3_bucket:
            local('s3cmd del --recursive s3://%(alt_s3_bucket)s/%(deployed_name)s' % env)
        run('rm -rf %(path)s')
