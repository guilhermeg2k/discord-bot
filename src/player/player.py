from asyncio import sleep
from datetime import timedelta
from os import getenv
from queue import Queue
from random import shuffle
from re import match

from discord import Embed, FFmpegPCMAudio
from discord.ext.commands import Context
from src.player.genius import GeniusApi
from src.player.songcache import SongCache
from src.player.youtube import (download_song, get_song_url,
                                get_youtube_playlist_songlist)


class Player():
    def __init__(self, bot) -> None:
        self.song_queue = {}
        self.current_song = {}
        self.bot = bot
        self.logger = bot.logger
        self.cache = SongCache(self.logger)
        self.IDLE_TIMEOUT = getenv("IDLE_TIMEOUT", 1)
        self.genius = GeniusApi(bot.logger)
        self.playing = False

    async def play(self, ctx: Context, play_text: str) -> None:
        if ctx.author.voice is None:
            await ctx.send("Você não está em um canal de voz")
            return

        user_voice_channel = ctx.author.voice.channel

        if ctx.voice_client is not None:
            if ctx.voice_client.channel != user_voice_channel:
                await ctx.send("O bot já está conectado em outro canal!")

        embed_msg = Embed(title=f":mag_right: **Procurando**: `{play_text}`",
                          color=0x550a8a)
        msg = await ctx.send(embed=embed_msg)

        await self.handle_song_request(play_text, ctx)
        if msg:
            await msg.delete()
        self.logger.info('Buscando a musica.')

    async def list(self, ctx: Context) -> None:
        queue = self.get_queue(ctx)
        if not queue.empty():
            list_buffer = ""
            queue_duration = 0
            for idx, song in enumerate(list(queue.queue), 1):
                list_buffer += f"**{idx}.** *" + song.title + "* " + \
                    f"`{timedelta(seconds=song.duration)}`" + \
                    f' {song.requester.mention}' + "\n"
                queue_duration += song.duration
            embed_msg = Embed(title=":play_pause: **Fila**",
                              description=list_buffer, color=0x550a8a)
            embed_msg.set_footer(
                text=f"Duração da fila: {str(timedelta(seconds=queue_duration))}")
            self.bot.loop.create_task(
                ctx.message.channel.send(embed=embed_msg))
            self.logger.info('O bot recuperou a fila de reprodução.')
        else:
            embed_msg = Embed(title="Fila vazia",
                              description="Adicione músicas :)", color=0xeb2828)
            self.bot.loop.create_task(
                ctx.message.channel.send(embed=embed_msg))
            self.logger.info(
                'O bot não recuperou a lista pois a fila está vazia.')

    async def leave(self, ctx: Context) -> None:
        user_voice_channel = ctx.author.voice.channel
        if ctx.voice_client and ctx.voice_client.channel == user_voice_channel:
            queue = self.get_queue(ctx)
            await self.send_commands_list(ctx)
            await ctx.voice_client.disconnect()
            with queue.mutex:
                queue.queue.clear()
            self.playing = False
            self.logger.info(
                f'O bot desconectou do canal.')
        else:
            self.bot.loop.create_task(
                ctx.send("O usuário deve estar no mesmo canal do bot para desconectá-lo"))

    async def pause(self, ctx: Context) -> None:
        if ctx.author.voice is not None:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                ctx.voice_client.pause()

    async def resume(self, ctx: Context) -> None:
        if ctx.author.voice is not None:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                ctx.voice_client.resume()

    async def next(self, ctx: Context) -> None:
        if ctx.author.voice is not None:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                ctx.voice_client.stop()

    async def play_queue(self, ctx: Context) -> None:
        self.playing = True
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        queue = self.get_queue(ctx)
        voice_client = ctx.voice_client
        idle_timer = 0
        self.logger.info('O bot está reproduzindo a fila.')
        current_playing_song_msg = None

        while idle_timer < self.IDLE_TIMEOUT:
            while not queue.empty():
                self.playing = True
                self.current_song[ctx.guild.id] = queue.get()

                await self.clear_channel(ctx)

                current_playing_song_embed_msg = Embed(title=f":arrow_forward: **Reproduzindo**",
                                                       description=f"`{self.current_song[ctx.guild.id].title}`", color=0x550a8a)
                current_playing_song_embed_msg.set_thumbnail(
                    url=self.current_song[ctx.guild.id].thumb)

                if self.current_song[ctx.guild.id].requester:
                    current_playing_song_embed_msg.set_footer(
                        text=f"Adicionada por {self.current_song[ctx.guild.id].requester.display_name}",
                        icon_url=self.current_song[ctx.guild.id].requester.avatar_url)

                current_playing_song_msg = await ctx.message.channel.send(embed=current_playing_song_embed_msg)

                voice_client.play(FFmpegPCMAudio(
                    self.current_song[ctx.guild.id].path))

                while voice_client.is_playing():
                    await sleep(1)

                self.playing = False
                idle_timer = 0
                del self.current_song[ctx.guild.id]

                if current_playing_song_msg:
                    await current_playing_song_msg.delete()

            await sleep(1)
            idle_timer += 1
        await self.send_commands_list(ctx)
        await voice_client.disconnect()
        self.logger.info('O bot desconectou do canal após reproduzir a fila.')
        return

    async def remove(self, ctx: Context, idx: str) -> None:
        """
        Remove song from the queue by index.
        """
        if ctx.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                queue = self.get_queue(ctx)
                if queue.empty():
                    embed_msg = Embed(title="Fila vazia",
                                      description="Adicione músicas :)", color=0xeb2828)
                    self.bot.loop.create_task(
                        ctx.message.channel.send(embed=embed_msg))
                    return
                if idx.isnumeric() and (abs(int(idx)) <= queue.qsize()):
                    del queue.queue[int(idx) - 1]
                    self.logger.info(
                        f'O bot removeu a música de posição {int(idx)-1} da fila.')
                else:
                    embed_msg = Embed(
                        title=f":x: **Posição inválida**", color=0xeb2828)
                    self.bot.loop.create_task(
                        ctx.message.channel.send(embed=embed_msg))
                    return

    async def clear(self, ctx: Context) -> None:
        """
        Clear queue.
        """
        if ctx.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                queue = self.get_queue(ctx)

                if queue.empty():
                    embed_msg = Embed(title="Fila vazia",
                                      description="Adicione músicas :)", color=0xeb2828)
                    self.bot.loop.create_task(
                        ctx.message.channel.send(embed=embed_msg))
                    return
                else:
                    with queue.mutex:
                        queue.queue.clear()
                    self.logger.info(f'O bot limpou a fila.')

    async def shuffle(self, ctx: Context) -> None:
        """
        Shuffle queue.
        """
        if ctx.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                queue = self.get_queue(ctx)

            if queue.empty():
                embed_msg = Embed(title="Fila vazia",
                                  description="Adicione músicas :)", color=0xeb2828)
                self.bot.loop.create_task(
                    ctx.message.channel.send(embed=embed_msg))
                return
            else:
                with queue.mutex:
                    shuffle(queue.queue)
                embed_msg = Embed(
                    title=":twisted_rightwards_arrows: **Fila embaralhada**", color=0x550a8a)
                self.bot.loop.create_task(
                    ctx.message.channel.send(embed=embed_msg))
                self.logger.info(f'O bot embaralhou a fila.')

    async def lyrics(self, ctx: Context, search_text: str = None) -> None:
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

    async def handle_song_request(self, play_text: str, ctx: Context,) -> None:
        is_youtube_playlist = match(
            "https://www.youtube.com/playlist*", play_text)
        is_youtube_link = match(
            "https://www.youtube.com/watch*|https://youtu.be/*", play_text)
        if is_youtube_playlist:
            await self.add_playlist(play_text, ctx)
        elif is_youtube_link:
            await self.add_song(play_text, ctx, link=True)
        else:
            await self.add_song(play_text, ctx)

    async def send_current_song_lyrics(self, ctx: Context) -> None:
        """
        Send lyrics from the current song.
        """
        current_song = self.current_song[ctx.guild.id]
        await self.send_lyrics_by_search_text(ctx, current_song.title)

    async def send_lyrics_by_search_text(self, ctx: Context, search_text: str = None) -> None:
        """
        Send lyrics by search text.
        """
        searching_embed_msg = Embed(title=f":mag_right: **Procurando letra da música**: `{search_text}`",
                                    color=0x550a8a)
        msg = await ctx.send(embed=searching_embed_msg)

        song = await self.genius.get_song_with_lyrics(search_text)
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

    async def send_commands_list(self, ctx: Context):
        commands_list_msg_description = "**-play** [-p] <nome da música> - Coloca uma música solicitada na fila\n\
            **-pause** [-ps] -  Pausa a música atual\n\
            **-resume** [-rs] - Voltar a tocar a música pausada\n\
            **-next** [-n] [-s] [-skip] - Pula para a proxima música na fila\n\
            **-list** [-ls] [-queue] [-q] - Exibi a fila de músicas a serem tocadas\n\
            **-shuffle** [-sf] - Embaralha a fila de músicas a serem tocadas\n\
            **-remove** [-r] <posição da música na fila>  - Remove uma música da fila\n\
            **-lyrics** [-ly] - Exibi a letra da música que está reproduzindo\n\
            **-lyrics** [-ly] <nome da música> - Exibi a letra da música solicitada\n\
            **-leave** [-l] - Me manda embora 😔\n"
        commands_list_msg_embed = Embed(title="🎶 **Lista de comandos**",
                                        description=commands_list_msg_description, color=0x550a8a)
        await ctx.send(embed=commands_list_msg_embed)

    async def add_playlist(self, play_list_url: str, ctx: Context) -> None:
        """
        Downloads all songs from a playlist and put them on que queue
        """
        songs_url = get_youtube_playlist_songlist(play_list_url)
        requester = ctx.message.author

        embed_msg = Embed(title=f":notepad_spiral: **Playlist adicionada a fila** :thumbsup:",
                          description=f"`{play_list_url}`", color=0x550a8a)
        embed_msg.set_footer(
            text=f"Adicionada por {requester.display_name}",
            icon_url=requester.avatar_url)

        self.bot.loop.create_task(ctx.message.channel.send(embed=embed_msg))
        for song_url in songs_url:
            await self.add_song(song_url, ctx, link=True, playlist=True)
        self.logger.info('O bot adicionou as músicas da playlist.')

    async def add_song(self, song_name: str, ctx: Context, link=False, playlist=False) -> None:
        """
        A parallel function to search, download the song and put on the queue
        Starts the player if it's not running
        """
        if not link:
            song_url = get_song_url(song_name)
        else:
            song_url = song_name

        id = str(match(r'.*watch\?v=(.*)', song_url).group(1))
        self.logger.info(f'ID:{id} \tURL:{song_url}')
        song = self.cache.get_song(id)
        if not song:
            self.logger.info('Musica nao encontrada em cache, baixando.')
            song = download_song(
                'songs', song_url, requester=ctx.message.author)
            if not song:
                self.logger.info('Música não encontrada')
                music_not_found_msg = Embed(title=f":x: **Música não encontrada**",
                                            color=0xeb2828)
                await ctx.message.channel.send(embed=music_not_found_msg)
                return
            self.cache.add_song(song)

        song.requester = ctx.message.author
        self.cache.increment_plays(id)
        queue = self.get_queue(ctx)
        queue.put(song)
        self.logger.info('Musica adicionada na fila de reproducao.')

        if self.playing:
            if not playlist:
                embed_msg = Embed(title=f":thumbsup: **Adicionado a fila de reprodução**",
                                  description=f"`{song.title}`", color=0x550a8a)
                embed_msg.set_footer(text=f"Posição: {len(queue.queue)}")
                self.bot.loop.create_task(
                    ctx.message.channel.send(embed=embed_msg))
            self.logger.info(
                'O bot adicionou a música na fila de reprodução.')
        else:
            self.playing = True
            self.bot.loop.create_task(self.play_queue(ctx))

    async def clear_channel(self, ctx):
        channel_msgs = await ctx.channel.history(limit=100).flatten()
        bot_channel_msgs = filter(lambda msg: msg.author == self.bot.user, channel_msgs)
        await ctx.channel.delete_messages(bot_channel_msgs)

    def get_queue(self, ctx: Context) -> Queue:
        """
        Checks if queue exists
        Create one if it does not
        Return if exists
        """
        if not ctx.guild.id in self.song_queue:
            self.song_queue[ctx.guild.id] = Queue()
        return self.song_queue[ctx.guild.id]

