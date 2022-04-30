import re


def scape_lyrics(lyrics: str) -> str:
    lyrics = lyrics.replace('URLCopyEmbedCopy', '') \
        .replace('leve1EmbedShare', '') \
        .replace('267EmbedShare', '')
    embed_pattern = r'\d*Embed|embed|EMBED$'
    lyrics = re.sub(embed_pattern, '', lyrics)
    return lyrics


def scape_song_title(song_title) -> str:
    parentheses_pattern = r'\(.*\)'
    ft_pattern = r'ft\..*'
    song_title = re.sub(parentheses_pattern, '', song_title)
    song_title = re.sub(ft_pattern, '', song_title)
    return song_title
