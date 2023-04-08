#!/usr/bin/python3

import datetime
import json
import requests
from pprint import pprint
import os
import re
import pytz
import time
import argparse

# from pydub import AudioSegment
# import logging
# import http.client
# from bs4 import BeautifulSoup

STREAM_URL = 'https://lsaplus.swisstxt.ch/audio/drs3_96.stream/'

def download_file(url, dir_name='audio'):
    local_filename = url.split('/')[-1]
    print('downloading ' + local_filename)
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(f'{dir_name}/{local_filename}', 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk:
                f.write(chunk)
    return local_filename


def download_last_minutes(minutes=10):
    """
    downloads the last minutes of the current SRF3 live stream, including metadata
    to a new directory
    :param minutes:
    :return:
    """

    ts_now = datetime.datetime.now(tz=pytz.timezone('Europe/Amsterdam'))
    ts_record = ts_now - datetime.timedelta(minutes=minutes)
    dir_name = ts_record.strftime("%Y-%m-%d_%H-%M")

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    url = 'https://www.srf.ch/programm/radio-api/lastplayed/radio-srf-3'
    r = requests.get(url)
    r.raise_for_status()
    lastplayed_data = r.json()

    songs = []
    for song in lastplayed_data['lastPlayedList']:
        ts = datetime.datetime.fromisoformat(song['timestamp'])
        if ts > ts_record - datetime.timedelta(minutes=5):
            songs.append(song)

    with open(f'{dir_name}.json', 'w') as f:
        json.dump(songs, f, indent=2)

    url = 'https://lsaplus.swisstxt.ch/audio/drs3_96.stream/chunklist_DVR.m3u8'
    download_file(url, dir_name)

    # Open the playlist file and read its contents into a variable
    with open(f'{dir_name}/chunklist_DVR.m3u8') as f:
        playlist = f.read()

    # Find all the media file names in the playlist
    media_files = re.findall(r'(media_DVR_\d+\.aac)', playlist)

    # Calculate the total duration of the playlist in milliseconds
    total_duration = sum(int(d) for d in re.findall(r'#EXTINF:(\d+)', playlist))

    duration = minutes * 60 * 1000  # in milliseconds

    current_duration = 0
    for media_file in reversed(media_files):
        download_file(f'https://lsaplus.swisstxt.ch/audio/drs3_96.stream/{media_file}', dir_name)
        current_duration += 10112
        if current_duration > duration:
            break
        else:
            time.sleep(0.5)

    # create a list of all .aac files in the directory
    file_list = [os.path.join(dir_name, f) for f in os.listdir(dir_name) if f.endswith('.aac')]

    # sort the file list alphabetically
    file_list.sort()

    # concatenate the files
    with open(f'{dir_name}.aac', 'wb') as outfile:
        for file_path in file_list:
            with open(file_path, 'rb') as infile:
                outfile.write(infile.read())


    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download the last minutes of the current SRF3 audio stream.')
    parser.add_argument('minutes', help='the number of minutes to download')
    args = parser.parse_args()
    download_last_minutes(args)

