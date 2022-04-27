from os import getenv

from discord import Embed
from discord.ext.commands import Context
from lyricsgenius import Genius
from requests import HTTPError, Timeout
from src.lyrics.lyrics_utils import scape_lyrics, scape_lyrics_search_str


class Lyrics():
    def __init__(self, bot) -> None:
        self.__genius_token = getenv('GENIUS_TOKEN')
        self.bot = bot
        self.logger = bot.logger
        self.player = bot.player
        self.__genius = None

        try:
            self.__genius = Genius(self.__genius_token, skip_non_songs=True, excluded_terms=[
                "(Remix)", "(Live)"], remove_section_headers=True, verbose=True)
        except HTTPError as e:
            self.logger.warning(
                f'Erro HTTP de status: {e.args[0]} com a mensagem: {e.args[1]}')
        except Timeout:
            self.logger.warning(f'Timeout')
        self.__genius = Genius(self.__genius_token, skip_non_songs=True, excluded_terms=[
            "(Remix)", "(Live)"], remove_section_headers=True, verbose=True)

    async def search_and_send(self, ctx: Context, search_text: str = None) -> None:
        """
        Send lyrics from the current song or from a search text using Genius API.
        """

        if search_text is None:
            self.bot.loop.create_task(
                self.send_current_song_lyrics(ctx)
            )
        else:
            self.bot.loop.create_task(
                self.send_lyrics_by_search_text(ctx, search_text=search_text)
            )

    async def get_song_with_lyrics(self, song_title: str = None) -> str:
        """
        Get song lyrics by song title
        """
        try:
            if self.__genius:
                song = self.__genius.search_song(
                    scape_lyrics_search_str(song_title))
        except HTTPError as e:
            self.logger.warning(
                f'Erro HTTP de status: {e.args[0]} com a mensagem: {e.args[1]}')
        except Timeout:
            self.logger.warning(f'Timeout')

        if song and song.lyrics:
            song.lyrics = scape_lyrics(song.lyrics)
            return song
        return None

    async def send_current_song_lyrics(self, ctx: Context) -> None:
        """
        Send lyrics from the player current song.
        """
        current_song = self.player.current_song[ctx.guild.id]
        await self.send_lyrics_by_search_text(ctx, current_song.title)

    async def send_lyrics_by_search_text(self, ctx: Context, search_text: str = None) -> None:
        """
        Send lyrics by search text.
        """
        searching_embed_msg = Embed(title=f":mag_right: **Procurando letra da música**: `{search_text}`",
                                    color=0x550a8a)
        msg = await ctx.send(embed=searching_embed_msg)

        song = await self.get_song_with_lyrics(search_text)
        if msg:
            await msg.delete()

        lyrics_embed_msg = ''
        if song and song.lyrics:
            self.logger.info(
                f'O bot enviou a lyrics ao canal')

            lyrics_embed_msg = Embed(title=f":pencil: **Lyrics**",
                                     description=f"**{song.title} by {song.artist}**\n\n{(song.lyrics)}",
                                     color=0x550a8a)
        else:
            self.logger.info(f'O bot não encontrou a lyrics.')

            lyrics_embed_msg = Embed(title=f":x: **Lyrics não encontrada**",
                                     color=0xeb2828)
        await ctx.message.channel.send(embed=lyrics_embed_msg)
