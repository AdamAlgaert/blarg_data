import logging
import requests
import jmespath
import os
from PIL import Image
import re
import numpy as np
import io
import pickle
from multiprocessing.pool import Pool

logger = logging.getLogger(__name__)

# Bachmanetti's google sheet with the user submitted image URLs
SPREADSHEET_SCRAPED_URL = 'https://spreadsheets.google.com/feeds/cells/1oyesB6iW5zYveN5C-qvwvxpMUCpwMOP7h6psa39mlsM/3/public/full?alt=json'
SCRAPED_JMES_FILTER = 'feed.entry[?"gs$cell".col==`"1"`].content."$t"'

def fetch_images():
    sheet_json = requests.get(SPREADSHEET_SCRAPED_URL).json()
    image_urls = jmespath.search(SCRAPED_JMES_FILTER, sheet_json)[1:]
    image_urls = [x for x in image_urls if x.startswith('http')]
    for url in image_urls:
        if not url.startswith('http'):
            return
        filename = url.split('/')[-1]
        local_filename = os.path.join('imgs', filename)
        if os.path.exists(local_filename):
            continue
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    f.write(r.content)
        except requests.exceptions.HTTPError as e:
            logger.error('%s', e)


def get_timing_array(filename):
    print('processing %s' % filename)
    output = []
    path = os.path.join('imgs', filename)
    with open(path, 'rb') as ifh:
        i = Image.open(io.BytesIO(ifh.read()))
    duration = 0
    for frame in range(0, i.n_frames):
        i.seek(frame)
        duration += i.info['duration']
    # for some reason, not all gifs are the same length according to PIL.Image
    # so for now we just drop images that are the wrong length.
    # sometimes download the same gif will result in different lengths, so this is probably a bug
    # on bungies end
    if duration != 19684800:
        return None
    for frame in range(0, i.n_frames):
        i.seek(frame)
        frame_color = True if i.convert('RGB').getpixel((0,0)) == (0,0,0) else False  # True for a black pixel
        frame_length = int(i.info['duration']/400)
        output = output + [frame_color] * frame_length
    return output


def get_all_timings():
    pool = Pool(4)
    filenames = os.listdir('imgs')
    res = filter(lambda x: x is not None, pool.map(get_timing_array, filenames))
    row = next(res)
    na = np.array([row])
    for row in res:
        na = np.append(na, [row], axis=0)
    return na


# processing the timing data takes a long time, so let's save it because it doesn't change much
def save_timing_data():
    timings = get_all_timings()
    with open('timing_data.bin', 'wb') as fh:
        pickle.dump(timings, fh)
    return timings


def get_timings():
    if os.path.exists('timing_data.bin'):
        with open('timing_data.bin') as fh:
            return pickle.load(fh)
    else:
        return save_timing_data()


def get_embedded_sequence_map():
    output_dict = {0: ' '}
    for filename in os.listdir('imgs'):
        path = os.path.join('imgs', filename)
        with open(path, 'rb') as ifh:
            fData = io.BytesIO(ifh.read())
        img = Image.open(fData)
        m = re.search("Data recovered: SEQ-(\d+) = '(.)'", img.info['comment'].decode())
        output_dict[int(m.group(1))] = m.group(2)
    return output_dict


def main():
    os.makedirs('imgs', exist_ok=True)
    fetch_images()
    frame_timings = get_timings()


    # image comments provide 30 unique SEQ-# to letter mappings
    seq_letter_map = get_embedded_sequence_map()
    # these 2 sequences are errors, so we remove them from the mapping
    del seq_letter_map[30045]  # h
    del seq_letter_map[12525]  # a

    # manually fill in letters here from context clues in the output
    # output position to character mapping
    seq_letter_map.update({
        23: 'a',
        36: 'k',
        42: 'h',
        74: 's',
        99: 'c',
        133: 'Z',
        143: 'v',
        159: 'x',
        177: 'g',
        197: 'V',
    })


    # frame pixel map to letter map
    letter_map = {}
    for k, v in seq_letter_map.items():
        letter_map[tuple(frame_timings.transpose()[k])] = v

    # frame pixel map to first occurrence position
    timing_to_position_map = {}
    for i, k in enumerate(frame_timings.transpose()):
        timing_to_position_map.setdefault(tuple(k), i)

    lore = ''
    for column in frame_timings.transpose():
        lore += letter_map.get(tuple(column), '<%s>' % timing_to_position_map[tuple(column)])
    print(lore.replace('^J', '\n').replace('^I', '\t').replace('^L', '\f'))


if __name__ == "__main__":
    main()
