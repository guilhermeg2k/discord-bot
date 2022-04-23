def scape_lyrics_search_str(search_str: str) -> str:
    search_str = search_str.lower()
    return search_str.replace('"', '""') \
    .replace('(', '') \
    .replace(')', '')  \
    .replace('lyric video', '') \
    .replace('official video', '')

def scape_lyrics(lyrics: str) -> str:
    return lyrics.replace('URLCopyEmbedCopy', '') \
    .replace('leve1EmbedShare', '') \
    .replace('267EmbedShare', '')