#!/usr/bin/env python

import json
import os

import boto
from boto.s3.key import Key
from tumblr import Api

MAX_POSTS = 10

if os.environ.get('DEPLOYMENT_TARGET', '') == 'production':
    S3_BUCKET = 'apps.npr.org'
else:
    S3_BUCKET = 'stage-apps.npr.org'

S3_KEY = 'live-results-election-2012'
TUMBLR_FILENAME = 'www/tumblr.json'
TUMBLR_BLOG_ID = 'nprbackchannel'

def push_to_s3():
    """
    Push current states CSV file to S3.
    """
    conn = boto.connect_s3()
    bucket = conn.get_bucket(S3_BUCKET)
    key = Key(bucket)
    key.key = S3_KEY
    key.set_contents_from_filename(
        TUMBLR_FILENAME,
        policy='public-read',
        headers={'Cache-Control': 'max-age=0 no-cache no-store must-revalidate'}
    )

def main():
    api = Api(TUMBLR_BLOG_ID)

    posts = list(api.read(max=MAX_POSTS))

    posts.reverse()

    with open(TUMBLR_FILENAME, 'w') as f:
        f.write(json.dumps(posts))

    push_to_s3()

    print 'Done'

if __name__ == '__main__':
    main()
