#!/usr/bin/env python

from fabric.api import *

import util

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


def load_bb_testing_rig():
    with settings(warn_only=True):
        local('rm electris.db')
        local('cp test_data/bigboard/electris_test.db electris.db')

        db = util.get_database()
        candidates = util.get_house_senate(db)
        util.write_house_json(candidates)
        util.write_senate_json(candidates)


def unload_bb_testing_rig():
    with settings(warn_only=True):
        local('rm electris.db')

        db = util.get_database()
        candidates = util.get_house_senate(db)
        util.write_house_json(candidates)
        util.write_senate_json(candidates)


def local_reset():

    # Nuke the local copies of everything.
    with settings(warn_only=True):
        local('rm www/states.csv')
        local('rm www/house.json')
        local('rm www/senate.json')
        local('rm www/president.json')
        local('rm electris.db')

    # Bootstrap the database.
    # This will create the DB if it doesn't exist.
    db = util.get_database()

    # Build the president CSV.
    states = util.get_states(db)
    util.regenerate_president(states)
    util.write_president_json(states)

    # Build the house/senate CSV.
    candidates = util.get_house_senate(db)
    util.write_house_json(candidates)
    util.write_senate_json(candidates)


def shiva_the_destroyer():
    """
    Deletes the app from s3
    """
    with settings(warn_only=True):
        local('s3cmd del --recursive s3://%(s3_bucket)s/%(project_name)s' % env)
        run('rm -rf %(path)s')
