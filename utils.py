from functools import wraps
import json

import yt_dlp

def load_config(config_file):
    with open(config_file, "r") as f:
        config = json.load(f)
    return config

def get_video_info(video_id):
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    with yt_dlp.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        video_title = info_dict.get('title', None)
        return video_title
    
def get_video_id(text):
    # Extract video id from youtube url or return video id
    if 'youtube.com' in text:
        video_id = text.split('v=')[-1]
    else:
        video_id = text
    return video_id