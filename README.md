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

* Data is updated every 4-6 minutes.
* Clients may connect once per minute.
* Clients must disconnect after each request.

Cron job:

```* * * * * $ENV_PATH/bin/python $REPO_PATH/fetch_ap_results.py```

Modes
-----

Electris can run in two modes: Forecasting and Election Night. Currently the mode can be set by toggling the ``IS_ELECTION_NIGHT`` variable at the top of ``app.js``.

