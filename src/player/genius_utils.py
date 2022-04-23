def scape_lyrics_search_str(ly_str: str) -> str:
    return ly_str.lower().replace('"', '""') \
    .replace('(', '') \
    .replace(')', '')  \
    .replace('lyric video', '') \
    .replace('official video', '')

def scape_lyrics(ly_str: str) -> str:
    return ly_str.replace('URLCopyEmbedCopy', '') \
    .replace('leve1EmbedShare', '') \
    .replace('267EmbedShare', '')