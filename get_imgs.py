#!/usr/bin/env python

import requests
import jmespath
import shutil
import os

# bachmanetti spreadsheet (Screaped Responses)
SPREADSHEET_SCRAPED_URL = 'https://spreadsheets.google.com/feeds/cells/1pD1or3qyg-PgT0Q_os-bTKwMr5WfoCY6CZ9AjAcpGqk/3/public/full?alt=json'
SCRAPED_JQ_FILTER = '.feed.entry[] | select(."gs$cell".col == "4" and ."gs$cell".row > "2") | .content."$t"'
SCRAPED_JMES_FILTER = 'feed.entry[?"gs$cell".col==`"4"` && "gs$cell".row>`"2"`].content."$t"'

SPREADSHEET_SRC_URL = 'https://spreadsheets.google.com/feeds/cells/1pD1or3qyg-PgT0Q_os-bTKwMr5WfoCY6CZ9AjAcpGqk/2/public/full?alt=json'
SRC_JQ_FILTER = '.feed.entry[] | select(."gs$cell".col == "5" and ."gs$cell".row > "1") | .content."$t"'
SRC_JMES_FILTER = 'feed.entry[?"gs$cell".col==`"5"` && "gs$cell".row>`"1"`].content."$t"'


def download_file(url):
    local_filename = os.path.join('imgs', url.split('/')[-1])
    if not os.path.exists(local_filename):
        with requests.get(url, stream=True) as r:
            with open(local_filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

    return local_filename


def main():
    os.makedirs('imgs', exist_ok=True)
    sheet_json = requests.get(SPREADSHEET_SRC_URL).json()
    image_urls = jmespath.search(SRC_JMES_FILTER, sheet_json)
    for url in image_urls:
        download_file(url)
    print(image_urls)


if __name__ == "__main__":
    main()
