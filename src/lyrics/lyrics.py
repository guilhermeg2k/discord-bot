from os import getenv

from discord import Embed
from discord.ext.commands import Context
from lyricsgenius import Genius
from requests import HTTPError, Timeout
from src.lyrics.lyrics_utils import scape_lyrics, scape_song_title
from src.utils import split_str_by_len


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
                self.send_song_lyrics(ctx, song_title=search_text)
            )

    async def get_song_with_lyrics(self, song_title: str = None, song_artist: str = None) -> str:
        """
        Get song lyrics by song title
        """
        try:
            if self.__genius:
                if song_artist:
                    artists = song_artist.split(',')
                    if len(artists) > 2:
                        song = self.__genius.search_song(
                            song_title, artists[0])
                    else:
                        song = self.__genius.search_song(
                            song_title, song_artist)
                else:
                    song = self.__genius.search_song(song_title)
        except HTTPError as e:
            self.logger.warning(
                f'Erro HTTP de status: {e.args[0]} com a mensagem: {e.args[1]}')
        except Timeout:
            self.logger.warning(f'Timeout')
            return await self.get_song_with_lyrics(song_title, song_artist)

        if song and song.lyrics:
            song.lyrics = scape_lyrics(song.lyrics)
            return song
        return None

    async def send_current_song_lyrics(self, ctx: Context) -> None:
        """
        Send lyrics from the player current song.
        """
        current_song = self.player.current_song[ctx.guild.id]
        if current_song.track:
            song_title = current_song.track
        else:
            song_title = current_song.title
        song_title = scape_song_title(song_title)
        print ('st', song_title)
        await self.send_song_lyrics(ctx, song_title , current_song.artist)

    async def send_song_lyrics(self, ctx: Context, song_title: str, song_artist: str = None) -> None:
        """
        Send song lyrics.
        """
        if song_artist:
            embed_msg_title = f":mag_right: **Procurando letra da música**: `{song_title}` by `{song_artist}`"
            searching_embed_msg = Embed(title=embed_msg_title,
                                        color=0x550a8a)
            msg = await ctx.send(embed=searching_embed_msg)
            song = await self.get_song_with_lyrics(song_title, song_artist)
        else:
            embed_msg_title = f":mag_right: **Procurando letra da música**: `{song_title}`"
            searching_embed_msg = Embed(title=embed_msg_title,
                                        color=0x550a8a)
            msg = await ctx.send(embed=searching_embed_msg)
            song = await self.get_song_with_lyrics(song_title)

        if msg:
            await msg.delete()

        paginated_lyrics = split_str_by_len(song.lyrics.strip(), 4000)
        pages = len(paginated_lyrics)
    
        if song and song.lyrics and pages <= 10:
            self.logger.info(
                f'O bot enviou a lyrics ao canal')
            lyrics_embed_msg = Embed(title=f":pencil: **Lyrics**",
                                     description=f"**{song.title} by {song.artist}**\n\n{(paginated_lyrics[0])}",
                                     color=0x550a8a)
            await ctx.message.channel.send(embed=lyrics_embed_msg)
            if pages > 1:
                page = 1
                while page < pages:
                    lyrics_embed_msg = Embed(description=paginated_lyrics[page],
                                             color=0x550a8a)
                    await ctx.message.channel.send(embed=lyrics_embed_msg)
                    page += 1
        else:
            self.logger.info(f'O bot não encontrou a lyrics.')
            lyrics_embed_msg = Embed(title=f":x: **Lyrics não encontrada**",
                                     color=0xeb2828)
            await ctx.message.channel.send(embed=lyrics_embed_msg)
