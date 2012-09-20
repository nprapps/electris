#!/usr/bin/env python

import boto
from boto.s3.key import Key

import cms_settings as settings

def push_results_to_s3():
    """
    Push current states CSV file to S3.
    """
    conn = boto.connect_s3()
    bucket = conn.get_bucket(settings.S3_BUCKET)
    key = Key(bucket)
    key.key = settings.S3_KEY
    key.set_contents_from_filename(
        settings.STATES_FILENAME,
        policy='public-read',
        headers={'Cache-Control': 'max-age=0 no-cache no-store must-revalidate'}
    )

if __name__ == "__main__":
    push_results_to_s3()

