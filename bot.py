import os
from discord.ext import commands
from discord import FFmpegPCMAudio
from dotenv import load_dotenv
from youtube import download_song, get_song_url
from queue import Queue
from asyncio import sleep

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
        async def play(ctx: commands.Context, *, song: str):
            if ctx.author.voice is None:
                await ctx.send("Você não está em um canal de voz")
                return

            user_voice_channel = ctx.author.voice.channel
            queue = self.get_queue(ctx)

            if ctx.voice_client is None:
                await user_voice_channel.connect()

            voice_client = ctx.voice_client
            if voice_client.channel == user_voice_channel:
                song_url = get_song_url(song)
                song_path = download_song('songs', song_url)
                queue.put(song_path)
                print(queue.qsize())  # Queue size

                if not voice_client.is_playing():
                    await self.play_queue(ctx)

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

    async def play_queue(self, ctx: commands.Context):
        queue = self.get_queue(ctx)
        voice_client = ctx.voice_client
        while not queue.empty():
            current_song_path = queue.get()
            print(f"Reproduzindo : {current_song_path}")
            voice_client.play(FFmpegPCMAudio(current_song_path))
            while voice_client.is_playing():
                await sleep(1)