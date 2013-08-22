Copyright 2013 NPR.  All rights reserved.  No part of these materials may be reproduced, modified, stored in a retrieval system, or retransmitted, in any form or by any means, electronic, mechanical or otherwise, without prior written permission from NPR.

(Want to use this code? Send an email to nprapps@npr.org!)

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

Polling data
----------------------

From 2012 Associated Press FTP docs:

* Data is updated every 4-6 minutes. (Verified with AP rep.)
* Clients may connect once per minute.
* Clients must disconnect after each request.

Cron jobs:

```
*/2 * * * * cd /home/ubuntu/apps/electris/repository && ../virtualenv/bin/fab production update_ap_data
* * * * * cd /home/ubuntu/apps/electris/repository && ../virtualenv/bin/fab production update_backchannel deploy_local_data backup_electris_db
```

Deploying from the Bitbucket backup repo
----------------------------------------

In the event Github is down, you can deploy from Bitbucket with the following:

```
git push bitbucket master
fab production master deploy:bitbucket
```

You must have had a user configured on Bitbucket for this to work!

