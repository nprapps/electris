from fabric.api import *

"""
Base configuration
"""
env.project_name = 'change-this-project-name-please'

"""
Environments
"""
def production():
    env.settings = 'production'
    env.s3_bucket = 'apps.npr.org'
    
def staging():
    env.settings = 'staging'
    env.s3_bucket = 'stage-apps.npr.org'

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
        if answer not in ('y','Y','yes','Yes','buzz off','screw you'):
            exit()

def _deploy_to_s3():
    """
    Deploy the gzipped stuff to
    """
    local(('s3cmd -P --add-header=Content-encoding:gzip --guess-mime-type --recursive sync gzip/ s3://%(s3_bucket)s/%(project_name)s/') % env)

def _gzip_www():
    """
    Gzips everything in www and puts it all in gzip
    """
    local('python gzip_www.py')

def deploy():
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])
    _confirm_branch()
    _gzip_www()
    _deploy_to_s3()

def shiva_the_destroyer():
    """
    Deletes the app from s3
    """
    with settings(warn_only=True):
        local('s3cmd del --recursive s3://%(s3_bucket)s/%(project_name)s' % env)
