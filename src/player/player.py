from asyncio import sleep
from datetime import timedelta
from os import getenv
from queue import Queue
from random import shuffle
from re import match, search
import traceback

from discord import Embed, FFmpegPCMAudio
from discord.ext.commands import Context
from discord.ui import Button, View, Modal, InputText
from discord import ButtonStyle, Interaction
from src.player.songcache import SongCache
from src.db.bot_sql import EVENT_TYPES
from src.player.youtube import (
    download_song,
    get_song_url,
    get_youtube_playlist_songlist,
)


class Player:

    def __init__(self, bot) -> None:
        self.song_queue = {}
        self.current_song = {}
        self.bot = bot
        self.logger = bot.logger
        self.cache = SongCache(self.logger)
        self.IDLE_TIMEOUT = int(getenv("IDLE_TIMEOUT", 1))
        self.playing = False
        self.player_msg = None

    async def play(self, ctx: Context, play_text: str) -> None:
        if ctx.author.voice is None:
            await ctx.respond(
                        embed=Embed(
                        title=f":x: **Você não está em um canal de voz!**",
                        color=0xEB2828),
                        delete_after=self.bot.delete_time)
            return

        user_voice_channel = ctx.author.voice.channel

        if ctx.voice_client is not None:
            if ctx.voice_client.channel != user_voice_channel:
                await ctx.respond(
                    embed=Embed(
                        title=f":x: **O bot já está conectado em outro canal!**",
                        color=0xEB2828),
                        delete_after=self.bot.delete_time
                    )
                return

        embed_msg = Embed(title=f":mag_right: **Procurando**: `{play_text}`",
                          color=0x550A8A)
        if ctx.message == self.player_msg:
            await ctx.respond(embed=embed_msg, ephemeral=True, delete_after=self.bot.delete_time)
        else:
            await ctx.respond(embed=embed_msg, ephemeral=True)

        self.logger.info("Buscando a musica.")
        await self.handle_song_request(play_text, ctx)

    async def list(self, ctx: Context) -> None:
        queue = self.get_queue(ctx)
        if not queue.empty():
            list_buffer = ""
            queue_duration = 0
            for idx, song in enumerate(list(queue.queue), 1):
                list_buffer += (f"**{idx}.** *" + song.title + "* " +
                                f"`{timedelta(seconds=song.duration)}`" +
                                f" {song.requester.mention}" + "\n")
                queue_duration += song.duration
            embed_msg = Embed(title=":play_pause: **Fila**",
                              description=list_buffer,
                              color=0x550A8A)
            embed_msg.set_footer(
                text=
                f"Duração da fila: {str(timedelta(seconds=queue_duration))}")
            self.bot.loop.create_task(
                ctx.respond(embed=embed_msg,
                            delete_after=self.bot.delete_time,
                            ephemeral=True))
            self.logger.info("O bot recuperou a fila de reprodução.")
        else:
            embed_msg = Embed(title="Fila vazia",
                              description="Adicione músicas :)",
                              color=0xEB2828)
            self.bot.loop.create_task(
                ctx.respond(embed=embed_msg,
                            delete_after=self.bot.delete_time))
            self.logger.info(
                "O bot não recuperou a lista pois a fila está vazia.")

    async def leave(self, ctx: Context) -> None:
        user_voice_channel = ctx.author.voice.channel
        if ctx.voice_client and ctx.voice_client.channel == user_voice_channel:
            await self.clear(ctx)
            await self.next(ctx)
            self.logger.info(f"O bot desconectou do canal.")
        else:
            self.bot.loop.create_task(
                ctx.respond(
                    embed=Embed(
                        title=f":x: **O Usuário deve estar no mesmo canal do bot para desconectá-lo**",
                        color=0xEB2828),
                    delete_after=self.bot.delete_time,
                ))
            
    async def btn_play_pause(self, iteraction: Interaction) -> None:
        ctx = await self.bot.get_application_context(iteraction)
        await iteraction.response.defer()
        if ctx.voice_client.is_paused():
            await self.resume(ctx)
            self.logger.info('Player resumido pelo botão')
        else: 
            await self.pause(ctx)
            self.logger.info('Player pausado pelo botão')
        
    async def btn_leave(self, iteraction: Interaction) -> None:
        ctx = await self.bot.get_application_context(iteraction)
        await iteraction.response.defer()
        await self.leave(ctx)
        self.logger.info('Bot removido pelo botão')

    async def btn_next(self, iteraction: Interaction) -> None:
        ctx = await self.bot.get_application_context(iteraction)
        await iteraction.response.defer()
        await self.next(ctx)
        self.logger.info('Próxima música pelo botão')

    async def btn_list(self, iteraction: Interaction) -> None:
        ctx = await self.bot.get_application_context(iteraction)
        await iteraction.response.defer()
        await self.list(ctx)
        self.logger.info('Listando pelo botão')

    async def btn_add(self, iteraction: Interaction) -> None:
        modal = Modal(title='Adicionar música na fila')
        modal.add_item(InputText(
            label='Nome ou link da música'
        ))
        modal.callback = self.modal_add
        await iteraction.response.send_modal(modal)
        self.logger.info('Modal enviada para o usuário')

    async def modal_add(self, iteraction: Interaction) -> None:
        resp = iteraction.data.get('components')

        if resp and len(resp) == 1:
            await iteraction.response.defer()
            text = resp[0].get('components')[0].get('value')
            ctx = await self.bot.get_application_context(iteraction)
            await self.play(ctx, play_text=text)

    async def pause(self, ctx: Context) -> None:
        if ctx.author.voice is not None:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                ctx.voice_client.pause()

                if self.player_msg:
                    embed_msg = Embed(
                        title=f":pause_button: **Pausado**",
                        description=
                        f"`{self.current_song[ctx.guild.id].title}`",
                        color=0x550A8A,
                    )
                    embed_msg.set_thumbnail(
                        url=self.current_song[ctx.guild.id].thumb)

                    if self.current_song[ctx.guild.id].requester:
                        embed_msg.set_footer(
                            text=
                            f"Adicionada por {self.current_song[ctx.guild.id].requester.display_name}",
                            icon_url=self.current_song[
                                ctx.guild.id].requester.avatar.url,
                        )

                    await self.player_msg.edit(embed=embed_msg)

    async def resume(self, ctx: Context) -> None:
        if ctx.author.voice is not None:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                ctx.voice_client.resume()

                if self.player_msg:
                    embed_msg = Embed(
                        title=f":arrow_forward: **Reproduzindo**",
                        description=
                        f"`{self.current_song[ctx.guild.id].title}`",
                        color=0x550A8A,
                    )
                    embed_msg.set_thumbnail(
                        url=self.current_song[ctx.guild.id].thumb)

                    if self.current_song[ctx.guild.id].requester:
                        embed_msg.set_footer(
                            text=
                            f"Adicionada por {self.current_song[ctx.guild.id].requester.display_name}",
                            icon_url=self.current_song[
                                ctx.guild.id].requester.avatar.url,
                        )

                    await self.player_msg.edit(embed=embed_msg)

    async def next(self, ctx: Context) -> None:
        if ctx.author.voice is not None:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                ctx.voice_client.stop()

    async def play_queue(self, ctx: Context) -> None:
        try:
            self.playing = True
            if ctx.voice_client is None:
                await ctx.author.voice.channel.connect()

            queue = self.get_queue(ctx)
            voice_client = ctx.voice_client
            idle_timer = 0
            self.logger.info("O bot está reproduzindo a fila.")

            while idle_timer < self.IDLE_TIMEOUT:
                while not queue.empty():
                    self.playing = True
                    self.current_song[ctx.guild.id] = queue.get()

                    current_playing_song_embed_msg = Embed(
                        title=f":arrow_forward: **Reproduzindo**",
                        description=
                        f"`{self.current_song[ctx.guild.id].title}`",
                        color=0x550A8A,
                    )
                    current_playing_song_embed_msg.set_thumbnail(
                        url=self.current_song[ctx.guild.id].thumb)

                    if self.current_song[ctx.guild.id].requester:
                        current_playing_song_embed_msg.set_footer(
                            text=
                            f"Adicionada por {self.current_song[ctx.guild.id].requester.display_name}",
                            icon_url=self.current_song[
                                ctx.guild.id].requester.avatar.url,
                        )

                    if self.player_msg:
                        self.player_msg = await self.player_msg.edit(
                            embed=current_playing_song_embed_msg)
                    else:
                        await self.create_btn_view()

                        self.player_msg = await ctx.channel.send(
                            embed=current_playing_song_embed_msg,
                            view=self.coltrol_view
                        )

                    voice_client.play(
                        FFmpegPCMAudio(self.current_song[ctx.guild.id].path))

                    while voice_client.is_playing() or voice_client.is_paused(
                    ):
                        bnt_next_disabled = self.coltrol_view.get_item('btn_next').disabled
                        btn_list = self.coltrol_view.get_item('btn_list')

                        if queue.empty():
                            if bnt_next_disabled == False or btn_list.disabled == False:
                                self.coltrol_view.get_item('btn_next').disabled = True
                                self.coltrol_view.get_item('btn_list').disabled = True
                                self.coltrol_view.get_item('btn_list').label = ""
                                await self.player_msg.edit(view=self.coltrol_view)
                        elif not queue.empty():
                            if bnt_next_disabled == True or btn_list.disabled == True or str(btn_list.label) != str(queue.qsize()):
                                self.coltrol_view.get_item('btn_next').disabled = False
                                self.coltrol_view.get_item('btn_list').disabled = False
                                self.coltrol_view.get_item('btn_list').label = str(queue.qsize())
                                await self.player_msg.edit(view=self.coltrol_view)
                        await sleep(1)

                    self.playing = False
                    idle_timer = 0
                    del self.current_song[ctx.guild.id]

                await sleep(1)
                idle_timer += 1

            await ctx.voice_client.disconnect()
            await self.player_msg.delete()
            self.player_msg = None
            self.logger.info(
                "O bot desconectou do canal após reproduzir a fila.")
        except Exception:
            error = str(traceback.format_exc())
            self.logger.error(error)
            await self.bot.send_exception(error, command='player')
        return
    
    async def create_btn_view(self) -> View:
        self.coltrol_view = View()
        
        btn_play_pause = Button(
            custom_id='btn_play_pause',

            style=ButtonStyle.primary, 
            emoji='⏯'
        )

        btn_next = Button(
            custom_id='btn_next',
            style=ButtonStyle.secondary,
            disabled=True,
            emoji='⏭'
        )

        btn_leave = Button(
            custom_id='btn_leave',
            style=ButtonStyle.danger, 
            emoji='👋'
        )
        
        btn_list = Button(
            custom_id='btn_list',
            style=ButtonStyle.secondary,
            disabled=True,
            emoji='📃'
        )

        btn_add = Button(
            custom_id='btn_add',
            style=ButtonStyle.success,
            emoji='➕'
        )

        btn_play_pause.callback = self.btn_play_pause
        btn_next.callback = self.btn_next
        btn_list.callback = self.btn_list
        btn_add.callback = self.btn_add
        btn_leave.callback = self.btn_leave

        self.coltrol_view.add_item(btn_play_pause)
        self.coltrol_view.add_item(btn_next)
        self.coltrol_view.add_item(btn_list)
        self.coltrol_view.add_item(btn_add)
        self.coltrol_view.add_item(btn_leave)
        return self.coltrol_view


    async def remove(self, ctx: Context, idx: int) -> None:
        """
        Remove song from the queue by index.
        """
        if ctx.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                queue = self.get_queue(ctx)
                if queue.empty():
                    embed_msg = Embed(
                        title="Fila vazia",
                        description="Adicione músicas :)",
                        color=0xEB2828,
                    )
                    self.bot.loop.create_task(
                        ctx.respond(embed=embed_msg,
                                    delete_after=self.bot.delete_time))
                if idx <= queue.qsize():
                    del queue.queue[idx - 1]
                    self.logger.info(
                        f"O bot removeu a música de posição {idx-1} da fila.")
                    self.bot.loop.create_task(
                        ctx.respond(embed=Embed(
                                        title=f":x: **Musica removida da fila**",
                                        color=0x169CCC),
                                    delete_after=self.bot.delete_time))
                else:
                    embed_msg = Embed(title=f":x: **Posição inválida**",
                                      color=0xEB2828)
                    self.bot.loop.create_task(
                        ctx.respond(embed=embed_msg,
                                    delete_after=self.bot.delete_time))

    async def clear(self, ctx: Context) -> bool:
        """
        Clear queue.
        """
        if ctx.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                queue = self.get_queue(ctx)

                if queue.empty():
                    return False
                else:
                    with queue.mutex:
                        queue.queue.clear()
                    self.logger.info(f"O bot limpou a fila.")
                    return True

    async def shuffle(self, ctx: Context) -> None:
        """
        Shuffle queue.
        """
        if ctx.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                queue = self.get_queue(ctx)

            if queue.empty():
                embed_msg = Embed(
                    title="Fila vazia",
                    description="Adicione músicas :)",
                    color=0xEB2828,
                )
                self.bot.loop.create_task(
                    ctx.respond(embed=embed_msg,
                                delete_after=self.bot.delete_time))
                return
            else:
                with queue.mutex:
                    shuffle(queue.queue)
                embed_msg = Embed(
                    title=":twisted_rightwards_arrows: **Fila embaralhada**",
                    color=0x550A8A,
                )
                self.bot.loop.create_task(
                    ctx.respond(embed=embed_msg,
                                delete_after=self.bot.delete_time))
                self.logger.info(f"O bot embaralhou a fila.")

    async def handle_song_request(self, play_text: str, ctx: Context) -> None:
        is_youtube_playlist = match(
            r"https:\/\/www\.youtube\.com\/playlist.*|https:\/\/youtube\.com\/playlist.*",
            play_text)
        is_youtube_link = match(
            r"https:\/\/www\.youtube\.com\/watch.*|https:\/\/youtu.be\/.*",
            play_text)
        if is_youtube_playlist:
            await self.add_playlist(play_text, ctx)
        elif is_youtube_link:
            await self.add_song(play_text, ctx, link=True)
        else:
            await self.add_song(play_text, ctx)

    async def add_playlist(self, play_list_url: str, ctx: Context) -> None:
        """
        Downloads all songs from a playlist and put them on que queue
        """
        songs_url = get_youtube_playlist_songlist(play_list_url)
        requester = ctx.author

        embed_msg = Embed(
            title=f":notepad_spiral: **Playlist adicionada a fila** :thumbsup:",
            description=f"`{play_list_url}`",
            color=0x550A8A,
        )
        embed_msg.set_footer(
            text=f"Adicionada por {requester.display_name}",
            icon_url=requester.avatar.url,
        )

        self.bot.loop.create_task(
            ctx.edit(embed=embed_msg, delete_after=self.bot.delete_time))
        for song_url in songs_url:
            await self.add_song(song_url, ctx, link=True, playlist=True)
        self.logger.info("O bot adicionou as músicas da playlist.")

    async def add_song(self,
                       song_name: str,
                       ctx: Context,
                       link=False,
                       playlist=False) -> None:
        """
        A parallel function to search, download the song and put on the queue
        Starts the player if it's not running
        """
        if not link:
            song_url = get_song_url(song_name)
        else:
            song_url = song_name

        result_id = search(r"youtube.com\/watch\?v=(.*)|youtu.be\/(.*)",
                           song_url)
        id = str(result_id.group(1) or result_id.group(2))

        self.logger.info(f"ID:{id} \tURL:{song_url}")
        song = self.cache.get_song(id)
        if not song:
            self.logger.info("Musica nao encontrada em cache, baixando.")
            song = download_song("songs", song_url, requester=ctx.author)
            if not song:
                self.logger.info("Música não encontrada")
                music_not_found_msg = Embed(
                    title=f":x: **Música não encontrada**", color=0xEB2828)
                await ctx.edit(embed=music_not_found_msg,
                               delete_after=self.bot.delete_time)
                return
            self.cache.add_song(song)

        song.requester = ctx.author
        self.cache.increment_plays(id)
        queue = self.get_queue(ctx)
        queue.put(song)
        self.logger.info("Musica adicionada na fila de reproducao.")
        self.bot.db.insert_event(ctx.author.id, EVENT_TYPES.MUSIC_PLAY.value, ctx.guild.id, id)

        if self.playing:
            if not playlist:
                embed_msg = Embed(
                    title=f":thumbsup: **Adicionado a fila de reprodução**",
                    description=f"`{song.title}`",
                    color=0x550A8A,
                )
                embed_msg.set_footer(text=f"Posição: {len(queue.queue)}")
                if ctx.message == self.player_msg:
                    self.bot.loop.create_task(
                        ctx.followup.send(
                            embed=embed_msg,
                            delete_after=self.bot.delete_time,
                            ephemeral=True
                        )
                    )
                else:
                    self.bot.loop.create_task(
                        ctx.edit(embed=embed_msg,
                                delete_after=self.bot.delete_time))
            self.logger.info("O bot adicionou a música na fila de reprodução.")
        else:
            self.playing = True
            await ctx.edit(delete_after=self.bot.delete_time)
            self.bot.loop.create_task(self.play_queue(ctx))

    def get_queue(self, ctx: Context) -> Queue:
        """
        Checks if queue exists
        Create one if it does not
        Return if exists
        """
        if not ctx.guild.id in self.song_queue:
            self.song_queue[ctx.guild.id] = Queue()
        return self.song_queue[ctx.guild.id]
