import os
from discord.ext import commands
from discord.player import FFmpegOpusAudio
from discord import FFmpegPCMAudio
from dotenv import load_dotenv
import youtube_dl

class Bot(commands.Bot):
    def __init__(self, command_prefix):
        super().__init__(command_prefix=command_prefix)
        load_dotenv()
        self.token = os.getenv('TOKEN')

        @self.event
        async def on_ready():
            print(f"{self.user.display_name} is connected")

        @self.command()
        async def join(ctx):
            if ctx.author.voice is None:
                await ctx.send("Você não está em um canal de voz")
                return
            
            voice_channel = ctx.author.voice.channel

            if ctx.voice_client is None:
                await voice_channel.connect()
            else:
                await ctx.voice_client.move_to(voice_channel)
        
        @self.command()
        async def play(ctx):
            voice_client = ctx.voice_client
            voice_client.stop()
            
            song_path = self.download_song('songs', "https://www.youtube.com/watch?v=-tn2S3kJlyU")

            voice_client.play(FFmpegPCMAudio(song_path))
            print(song_path)

        @self.command()
        async def pause(ctx):
            voice_client = ctx.voice_client
            voice_client.pause()
            
        @self.command()
        async def resume(ctx):
            voice_client = ctx.voice_client
            voice_client.resume()

        self.run(self.token)

    def download_song(self, folder, url):
        # Download the music
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{folder}/%(id)s.%(ext)s',
            }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            song_info = ydl.extract_info(url)
            file_name = f'{song_info["id"]}.webm'
            ydl.download([url])
        return f'{folder}/{file_name}'