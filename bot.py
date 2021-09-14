import os
from discord.ext import commands
from discord import FFmpegPCMAudio
from dotenv import load_dotenv
from youtube import download_song, get_song_url

class Bot(commands.Bot):
    def __init__(self, command_prefix):
        super().__init__(command_prefix=command_prefix)
        load_dotenv()
        self.token = os.getenv('TOKEN')

        @self.event
        async def on_ready():
            print(f"{self.user.display_name} is connected")
        
        @self.command()
        async def play(ctx, *, song):
            if ctx.author.voice is None:
                await ctx.send("Você não está em um canal de voz")
                return
            
            voice_channel = ctx.author.voice.channel
            
            if ctx.voice_client is None:
                await voice_channel.connect()
 
            voice_client = ctx.voice_client
            if voice_client.channel == voice_channel:
                voice_client.stop()
                song_url = get_song_url(song)
                song_path = download_song('songs', song_url)
                voice_client.play(FFmpegPCMAudio(song_path))
            else:
                await ctx.send("O bot já está conectado em outro canal!")

        @self.command()
        async def pause(ctx):
            voice_client = ctx.voice_client
            voice_client.pause()
            
        @self.command()
        async def resume(ctx):
            voice_client = ctx.voice_client
            voice_client.resume()

        self.run(self.token)
