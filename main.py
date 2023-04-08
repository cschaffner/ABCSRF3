#!/usr/bin/python3

import datetime
import json
import requests
from pprint import pprint
import os
import re
import pytz
import time
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


def download_chunks(start, end=False):
    """
    downloads audio live stream chunks from start to end and stores them
    :param i:
    :return:
    """
    if end == False:
        end = start + 20

    for i in range(start, end):
        download_file(STREAM_URL + f'/media_DVR_{i}.aac')


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


def test_SRF():
    url = 'https://www.srf.ch/programm/radio-api/lastplayed/radio-srf-3'
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    pprint(data)

    url = 'https://il.srgssr.ch/integrationlayer/2.0/mediaComposition/byUrn/urn:srf:audio:dd0fa1ba-4ff6-4e1a-ab74-d7e49057d96f.json?onlyChapters=false&vector=portalplay'
    r = requests.get(url)
    r.raise_for_status()
    lastplayed_data = r.json()


    pprint(data)


    url = 'https://lsaplus.swisstxt.ch/audio/drs3_96.stream/playlist.m3u8'
    url = 'https://lsaplus.swisstxt.ch/audio/drs3_96.stream/chunklist_DVR.m3u8'

    # download_file(url)


    url = 'https://lsaplus.swisstxt.ch/audio/drs3_96.stream/chunklist_DVR.m3u8'

    # download_chunks(383892)

    # define the audio fragment you are looking for
    # fragment = AudioSegment.from_file("news_jingle.aac", format="aac")

    # specify the directory containing the AAC files
    directory = "audio/"

    start = 384240
    # combined_sound = AudioSegment.from_file(f"audio/media_DVR_{start}.aac", format="aac")

    with open("audio/concatenated.aac", "wb") as concatenated:
        for i in range(1, 20):
            with open(f"audio/media_DVR_{start + i}.aac", "rb") as file:
                concatenated.write(file.read())


    #
    # # print(combined_sound.raw_data[:2000])
    # # print(combined_sound.raw_data[2000:4000])
    # #
    # for i in range(1,20):
    #     combined_sound = combined_sound.append(AudioSegment.from_file(f"audio/media_DVR_{start+i}.aac", format="aac"), crossfade=100)
    #
    # combined_sound.export("combined.aac", format="adts")


    # r = requests.get(url)
    # r.raise_for_status()
    # data = r.json()
    # pprint(data)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    download_last_minutes(10)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
