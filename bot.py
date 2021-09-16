import os
from discord.ext import commands
from discord import FFmpegPCMAudio
from dotenv import load_dotenv
from youtube import download_song, get_song_url
from queue import Queue
from asyncio import sleep
from song import Song
from datetime import timedelta
from threading import Thread

class Bot(commands.Bot):
    def __init__(self, command_prefix: str):
        super().__init__(command_prefix=command_prefix)
        load_dotenv()
        self.token = os.getenv('TOKEN')
        self.song_queue = {}

        @self.event
        async def on_ready():
            print(f"{self.user.display_name} is connected")

        @self.command()
        async def play(ctx: commands.Context, *, song_name: str):
            if ctx.author.voice is None:
                await ctx.send("Você não está em um canal de voz")
                return

            user_voice_channel = ctx.author.voice.channel
            queue = self.get_queue(ctx)

            if ctx.voice_client is None:
                await user_voice_channel.connect()

            voice_client = ctx.voice_client
            if voice_client.channel == user_voice_channel:
                song_handler = Thread(
                    target=self.add_song, args=(song_name, ctx))
                song_handler.daemon = True
                song_handler.start()

            else:
                await ctx.send("O bot já está conectado em outro canal!")

        @self.command()
        async def pause(ctx: commands.Context):
            voice_client = ctx.voice_client
            voice_client.pause()

        @self.command()
        async def next(ctx: commands.Context):
            voice_client = ctx.voice_client
            voice_client.stop()

        @self.command()
        async def resume(ctx: commands.Context):
            voice_client = ctx.voice_client
            voice_client.resume()

        @self.command()
        async def leave(ctx: commands.Context):
            user_voice_channel = ctx.author.voice.channel
            voice_client = ctx.voice_client
            if voice_client.channel == user_voice_channel:
                await voice_client.disconnect()

        @self.command()
        async def list(ctx: commands.Context):
            queue = self.get_queue(ctx)
            list_buffer = "```Fila de músicas:\n"
            queue_duration = 0 
            for idx, song in enumerate(queue.queue, 1):
                list_buffer += f"{idx} - " + song.title + "\t: " + str(timedelta(seconds=song.duration)) + "\n"
                queue_duration += song.duration
            list_buffer += f"Duração da fila: {str(timedelta(seconds=queue_duration))}```"
            await ctx.message.channel.send(list_buffer)

        self.run(self.token)
    def get_queue(self, ctx: commands.Context) -> Queue:
        """
        Checks if queue exists
        Create one if it does not
        Return if exists
        """
        self.song_queue                               #TODO Check channel id
        if not ctx.guild.id in self.song_queue:
            self.song_queue[ctx.guild.id] = Queue()

        return self.song_queue[ctx.guild.id]

    async def play_queue(self, ctx: commands.Context) -> None:
        queue = self.get_queue(ctx)
        voice_client = ctx.voice_client
        while not queue.empty():
            current_song = queue.get()
            await ctx.message.channel.send(f"```Reproduzindo: \n{current_song.title} adicionada por {current_song.requester}```")
            voice_client.play(FFmpegPCMAudio(current_song.path))
            while voice_client.is_playing():
                await sleep(1)

    def add_song(self, song_name: str, ctx: commands.Context) -> None:
        """
        A parallel function to search, download the song and put on the queue
        Starts the player if it's not running
        """
        song_url = get_song_url(song_name)
        song = download_song('songs', song_url)
        song.set_requester(ctx.message.author.display_name)
        queue = self.get_queue(ctx)
        queue.put(song)
        if ctx.voice_client.is_playing():
            self.loop.create_task(ctx.message.channel.send(
                f"```Adicionado a fila de reprodução:\n{song.title}\nPosição: {len(queue.queue)}```"))
        else:
            self.loop.create_task(self.play_queue(ctx))
