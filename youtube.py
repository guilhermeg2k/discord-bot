from logging import exception
from typing import Dict, List
import youtube_dl
import urllib.request
import re
from song import Song

def download_song(folder: str, url: str) -> Song:
    """
        Download a video from youtube
        Return a Song class with the music data
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{folder}/%(id)s.%(ext)s',
    }
    try:
        ydl = youtube_dl.YoutubeDL(ydl_opts)
        song_info = ydl.extract_info(url)
        new_song = Song(song_info)
        new_song.set_folder(folder)
        #file_name = f'{song_info["id"]}.{song_info["ext"]}'
        ydl.download([url])
        return new_song
    except:
        raise(f'Failed to download song url: {url}')

def get_song_url(song: str) -> str:
    """
        Search for a song on youtube
        and return its url
    """
    is_spotify_url = re.match("https://open.spotify.com/track/.*", song)
    if is_spotify_url:
        return get_song_url_from_spotify(song)
    else:
        return get_song_youtube_url(song)

def get_song_youtube_url(song_query: str) -> str:
    """
        Search for a song query on youtube
        and return its url
    """
    try:
        song_query = urllib.parse.quote_plus(song_query)
        html = urllib.request.urlopen(
            f"https://www.youtube.com/results?search_query={song_query}")
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        return f'https://www.youtube.com/watch?v={video_ids[0]}'
    except:
        raise Exception(f'Failed to get video url to the song "{song_query}"')


def get_song_url_from_spotify(url: str) -> str:
    """
        Search for song on on youtube
        by a spotify track url
        and return its url
    """
    try:
        html = urllib.request.urlopen(url)
        html_decoded = html.read().decode()
        song_info = re.findall(r"<h1.*>.*<span.*>(.*)</span.*></h1>", html_decoded)
        song_url = get_song_youtube_url(f'{song_info[0]} {song_info[1]}')
        return song_url
    except:
        raise Exception(f'Failed to get a video url from a spotify track with url: "{url}"')

def get_youtube_playlist_songlist(url: str) -> List[str]:
    """
        Returns an array of videos urls 
        from a youtube playlist url
    """
    try:
        html = urllib.request.urlopen(url)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        video_ids = list(dict.fromkeys(video_ids))
        if len(video_ids) > 0:
            video_urls = []
            for id in video_ids:
                video_urls.append(f'https://www.youtube.com/watch?v={id}')
            return video_urls
        else:
            raise Exception(f'No videos ids founded on url {url}')
    except:
        raise Exception(f'Failed to get songlist from playlist with url: "{url}"')