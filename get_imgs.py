#!/usr/bin/env python

import logging
import requests
import jmespath
import shutil
import os
import sqlite3
import hashlib

# bachmanetti spreadsheet (Screaped Responses)
SPREADSHEET_SCRAPED_URL = 'https://spreadsheets.google.com/feeds/cells/1pD1or3qyg-PgT0Q_os-bTKwMr5WfoCY6CZ9AjAcpGqk/3/public/full?alt=json'
# SCRAPED_JQ_FILTER = '.feed.entry[] | select(."gs$cell".col == "4" and ."gs$cell".row > "2") | .content."$t"'
SCRAPED_JMES_FILTER = 'feed.entry[?"gs$cell".col==`"4"` && "gs$cell".row>`"2"`].content."$t"'

SPREADSHEET_SRC_URL = 'https://spreadsheets.google.com/feeds/cells/1pD1or3qyg-PgT0Q_os-bTKwMr5WfoCY6CZ9AjAcpGqk/2/public/full?alt=json'
# SRC_JQ_FILTER = '.feed.entry[] | select(."gs$cell".col == "5" and ."gs$cell".row > "1") | .content."$t"'
SRC_JMES_FILTER = 'feed.entry[?"gs$cell".col==`"5"` && "gs$cell".row>`"1"`].content."$t"'
EARLY_ACCESS_DENIED_MD5 = 'e1d4105c8bcd488c5f452ec5fb5e8739'

logger = logging.getLogger(__name__)


def find_next_filename(filename):
    counter = 1
    path, name = os.path.split(filename)
    new_name = os.path.join(path, '%s-%s' % (counter, name))
    while os.path.exists(new_name):
        counter += 1
        new_name = os.path.join(path, '%s-%s' % (counter, name))
    return new_name


def download_file(url):
    logger.info('Fetching %s', url)
    local_filename = os.path.join('imgs', url.split('/')[-1])
    if os.path.exists(local_filename):
        with open(local_filename, 'rb') as f:
            existing_hash = hashlib.md5(f.read())
    else:
        existing_hash = ''
    try:
        with requests.get(url) as r:
            r.raise_for_status()
            new_hash = hashlib.md5(r.content).hexdigest()
            if new_hash == existing_hash or new_hash == EARLY_ACCESS_DENIED_MD5:
                return
            if existing_hash and existing_hash != new_hash and existing_hash != EARLY_ACCESS_DENIED_MD5:
                backup_filename = find_next_filename(local_filename)
                os.rename(local_filename, backup_filename)
                logger.warning('Image hash changed for existing file.  Backing up %s to %s', local_filename, backup_filename)
            with open(local_filename, 'wb') as f:
                f.write(r.content)
    except requests.exceptions.HTTPError as e:
        logger.error('%s', e)


def main():
    os.makedirs('imgs', exist_ok=True)
    sheet_json = requests.get(SPREADSHEET_SRC_URL).json()
    image_urls = jmespath.search(SRC_JMES_FILTER, sheet_json)
    for url in image_urls:
        download_file(url)


if __name__ == "__main__":
    main()
