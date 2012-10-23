electris
========

Server environment
------------------

The following environment variables must be defined:

* ``DEPLOYMENT_TARGET`` ("production" to disable DEBUG mode)
* ``AWS_ACCESS_KEY_ID`` (for boto)
* ``AWS_SECRET_ACCESS_KEY`` (for boto)
* ``AP_USERNAME`` (for FTP)
* ``AP_PASSWORD`` (for FTP)

Polling AP data
----------------------

From 2012 FTP docs:

* Data is updated every 4-6 minutes. (Verified with AP rep.)
* Clients may connect once per minute.
* Clients must disconnect after each request.

Cron job:

```*/1  * * * * cd /home/ubuntu/apps/electris/repository && ../virtualenv/bin/python fetch_ap_results.py```

Our contact at the AP is Tracy Lewis <tllewis@ap.org> (the two l's are not a typo).

Deploying prediction data
-------------------------

Changes to the election predictions should be made in ``states_bootstrap.csv`` first. You can then regenerate your local database by running:

```fab reset_local_data```

Finally, you can deploy your local data file by running:

```fab [staging|production] master deploy_local_data```

