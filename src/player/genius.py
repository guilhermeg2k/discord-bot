from os import getenv
from lyricsgenius import Genius
from requests import HTTPError, Timeout

from src.player.genius_utils import scape_lyrics, scape_lyrics_search_str

class GeniusApi:
    def __init__(self, logger) -> None:
        self.__genius_token = getenv('GENIUS_TOKEN')
        self.__logger = logger
        try:
            self.__genius = Genius(self.__genius_token, skip_non_songs=True, excluded_terms=[
                "(Remix)", "(Live)"], remove_section_headers=True, verbose=True)
        except HTTPError as e:
            logger.warning(
                f'Erro HTTP de status: {e.args[0]} com a mensagem: {e.args[1]}')
        except Timeout:
            self.__logger.warning(f'Timeout')
        self.__genius = Genius(self.__genius_token, skip_non_songs=True, excluded_terms=[
            "(Remix)", "(Live)"], remove_section_headers=True, verbose=True)

    async def get_song_with_lyrics(self, song_title: str = None) -> str:
        """
        Get song lyrics by song title
        """
        try:
            if self.__genius:
                song = self.__genius.search_song(
                    scape_lyrics_search_str(song_title))
        except HTTPError as e:
            self.__logger.warning(
                f'Erro HTTP de status: {e.args[0]} com a mensagem: {e.args[1]}')
        except Timeout:
            self.__logger.warning(f'Timeout')

        if song and song.lyrics:
            song.lyrics = scape_lyrics(song.lyrics)
            return song
        return None
