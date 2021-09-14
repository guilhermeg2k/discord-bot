from logging import exception
import youtube_dl
import urllib.request
import re

def download_song(folder, url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{folder}/%(id)s.%(ext)s',
            }
        try:
            ydl = youtube_dl.YoutubeDL(ydl_opts)
            song_info = ydl.extract_info(url)
            file_name = f'{song_info["id"]}.{song_info["ext"]}'
            ydl.download([url])
            return f'{folder}/{file_name}'
        except:
            raise(f'Failed to download song url: {url}')

def get_song_url(song_query):
    try:
        song_query = urllib.parse.quote_plus(song_query)
        html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={song_query}")
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        return f'https://www.youtube.com/watch?v={video_ids[0]}'
    except:
        raise Exception(f'Failed to get video url to the song "{song_query}"')