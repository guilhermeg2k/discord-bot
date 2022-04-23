def transform_ly_search_str(ly_str: str) -> str:
    return ly_str.replace('"', '""') \
    .replace('(', '') \
    .replace(')', '')  \
    .replace('Lyric Video', '') \
    .replace('Official Video', '')

def transform_ly_str(ly_str: str) -> str:
    return ly_str.replace('URLCopyEmbedCopy', '') \
    .replace('leve1EmbedShare', '') \
    .replace('267EmbedShare', '')