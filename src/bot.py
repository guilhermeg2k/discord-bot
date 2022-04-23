import os

from discord import Activity, ActivityType
from discord.ext import commands
from dotenv import load_dotenv

from src.logger import Logger
from src.player.player import Player


class Bot(commands.Bot):
    def __init__(self, command_prefix: str):
        super().__init__(command_prefix=command_prefix)
        self.logger = Logger().get_logger()
        self.logger.info('Iniciando Bot.')
        load_dotenv()
        self.token = os.getenv('TOKEN')
        self.player = Player(bot=self)

        @self.event
        async def on_ready():
            self.logger.info('Bot conectado com o Discord.')
            self.loop.create_task(self.change_presence(activity=Activity(
                type=ActivityType.listening, name="no -play, tchama ♫")))

        @self.command(aliases=['p'])
        async def play(ctx: commands.Context, *, play_text: str):
            self.logger.info('O bot recebeu uma solicitacao de play.')
            await self.player.play(ctx, play_text)

        @self.command()
        async def pause(ctx: commands.Context):
            await __delete_message__(ctx)
            await self.player.pause(ctx)
            self.logger.info('O bot pausou a música.')

        @self.command(aliases=['n', 's', 'skip'])
        async def next(ctx: commands.Context):
            await __delete_message__(ctx)
            await self.player.next(ctx)
            self.logger.info('O bot pulou a música.')

        @self.command(aliases=['rs'])
        async def resume(ctx: commands.Context):
            await __delete_message__(ctx)
            await self.player.resume(ctx)
            self.logger.info('O bot voltou a reproduzir a música.')

        @self.command(aliases=['l'])
        async def leave(ctx: commands.Context):
            await __delete_message__(ctx)
            await self.player.leave(ctx)
            self.logger.info('O bot saiu do canal de voz.')

        @self.command(aliases=['q', 'queue'])
        async def list(ctx: commands.Context):
            await __delete_message__(ctx)
            await self.player.list(ctx)
            self.logger.info('O bot listou a fila de reprodução.')

        @self.command(aliases=['r'])
        async def remove(ctx: commands.Context, *, idx: str):
            await __delete_message__(ctx)
            await self.player.remove(ctx, idx)

        @self.command(aliases=['c', 'clean'])
        async def clear(ctx: commands.Context):
            await __delete_message__(ctx)
            await self.player.clear(ctx)

        @self.command()
        async def shuffle(ctx: commands.Context):
            await __delete_message__(ctx)
            await self.player.shuffle(ctx)

        @self.command(aliases=['ly'])
        async def lyrics(ctx: commands.Context, *, search_text: str = None):
            await self.player.lyrics(ctx, search_text=search_text)

        @self.command()
        async def ping(ctx: commands.Context):
            await ctx.send("Pong!")

        async def __delete_message__(ctx: commands.Context):
            await ctx.message.delete()

        self.run(self.token)
