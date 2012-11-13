#!/usr/bin/env python

import datetime
import json
from time import sleep

import boto
from boto.s3.key import Key
from fabric.api import *
from peewee import *
from tumblr import Api
import requests

import input as i
from models import Candidate, Race, State
import output as o

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
    env.s3_bucket = 'election2012.npr.org'
    env.alt_s3_bucket = 'election2012-alt.npr.org'
    env.hosts = ['cron.nprapps.org']


def staging():
    env.settings = 'staging'
    env.s3_bucket = 'stage-election2012.npr.org'
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
    build()
    local(('\
        s3cmd -P\
        --add-header=Cache-control:max-age=5\
        --add-header=Content-encoding:gzip\
        --guess-mime-type\
        --recursive\
        --exclude *.json\
        sync gzip/ s3://%(s3_bucket)s/') % env)
    if env.alt_s3_bucket:
        local(('\
            s3cmd -P\
            --add-header=Cache-control:max-age=5\
            --add-header=Content-encoding:gzip\
            --guess-mime-type\
            --recursive\
            --exclude *.json\
           sync  gzip/ s3://%(alt_s3_bucket)s/') % env)


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


def setup_database():
    sudo('echo "CREATE USER electris WITH PASSWORD \'electris\';" | psql', user='postgres')
    sudo('createdb -O electris electris', user='postgres')


def clone_repo():
    require('settings', provided_by=[production, staging])

    run('git clone git@github.com:nprapps/%(project_name)s.git %(repo_path)s' % env)
    run('git remote add bitbucket git@bitbucket.org:nprapps/%(project_name)s.git' % env)


def checkout_latest(remote='origin'):
    require('settings', provided_by=[production, staging])

    env.remote = remote

    run('cd %(repo_path)s; git fetch %(remote)s' % env)
    run('cd %(repo_path)s; git checkout %(branch)s; git pull %(remote)s %(branch)s' % env)


def install_requirements():
    require('settings', provided_by=[production, staging])

    run('%(virtualenv_path)s/bin/pip install -r %(repo_path)s/requirements.txt' % env)


def deploy(remote='origin'):
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])
    _confirm_branch()
    _gzip_www()
    _deploy_to_s3()

    with settings(warn_only=True):
            sudo('service electris_cms stop')
            sudo('service electris_cron stop')

    checkout_latest(remote)

    sudo('service electris_cms start')
    sudo('service electris_cron start')


def deploy_local_data():
    """
    Deploy the local data files to S3.
    """
    require('settings', provided_by=[production, staging])
    write_www_files()
    _gzip_www()
    local(('s3cmd -P --add-header=Cache-control:max-age=5 --add-header=Content-encoding:gzip --guess-mime-type put gzip/*.json s3://%(s3_bucket)s/') % env)
    if env.alt_s3_bucket:
        local(('s3cmd -P --add-header=Cache-control:max-age=5 --add-header=Content-encoding:gzip --guess-mime-type put gzip/*.json s3://%(alt_s3_bucket)s/') % env)


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
    local('sudo -u postgres pg_dump -f /tmp/electris_backup.sql -Fp -E UTF8 --inserts electris')
    local('s3cmd -P  --add-header=Cache-control:max-age=5 --guess-mime-type put /tmp/electris_backup.sql s3://%(s3_bucket)s/' % env)
    if env.alt_s3_bucket:
        local('s3cmd -P  --add-header=Cache-control:max-age=5 --guess-mime-type put /tmp/electris_backup.sql s3://%(alt_s3_bucket)s/' % env)


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
        key.key = TUMBLR_FILENAME
        key.set_contents_from_filename(
            TUMBLR_FILENAME,
            policy='public-read',
            headers={'Cache-Control': 'max-age=5 no-cache no-store must-revalidate'}
        )
        if env.alt_s3_bucket:
            conn = boto.connect_s3()
            bucket = conn.get_bucket(env.alt_s3_bucket)
            key = Key(bucket)
            key.key = TUMBLR_FILENAME
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


def build():
    local('webassets -m assets_env build')


def watch():
    local('webassets -m assets_env watch')


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
        sudo('dropdb electris', user='postgres')
        sudo('createdb -O electris electris', user='postgres')
        sudo('cat initial_data/initial_psql.sql | psql -q electris', user='postgres')
        write_www_files()
        sudo('service electris_cms start')
        sudo('service electris_cron start')


def local_reset():
    """
    Resets the local environment to a fresh copy of the db and data.
    """
    with settings(warn_only=False):
        local('dropdb electris')
        local('echo "CREATE USER electris WITH PASSWORD \'electris\';" | psql')

    local('createdb -O electris electris')
    local('cat initial_data/initial_psql.sql | psql -q electris')

    write_www_files()


def local_latest():
    """
    Resets the local DB to the latest version from S3.
    """
    db_text = requests.get('http://election2012.npr.org.s3.amazonaws.com/electris_backup.sql')
    if db_text.status_code == 200:
        with open('initial_data/electris_backup.sql', 'w') as f:
            f.write(db_text.content)

    with settings(warn_only=False):
        local('dropdb electris')
        local('echo "CREATE USER electris WITH PASSWORD \'electris\';" | psql')

    local('createdb -O electris electris')
    local('cat initial_data/electris_backup.sql | psql -q electris')


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
    local('s3cmd -P --add-header=Cache-control:max-age=5 put initial_data/' + filename + ' s3://%(s3_bucket)s/status.json' % env)
    if env.alt_s3_bucket:
        local('s3cmd -P --add-header=Cache-control:max-age=5 put initial_data/' + filename + ' s3://%(alt_s3_bucket)s/status.json' % env)


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
        local('s3cmd del --recursive s3://%(s3_bucket)s' % env)
        if env.alt_s3_bucket:
            local('s3cmd del --recursive s3://%(alt_s3_bucket)s' % env)
        run('rm -rf %(path)s')
