import os
from discord.ext import commands
from discord import Activity, ActivityType
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
            await self.player.pause(ctx)
            self.logger.info('O bot pausou a música.')

        @self.command(aliases=['n', 's', 'skip'])
        async def next(ctx: commands.Context):
            await self.player.next(ctx)
            self.logger.info('O bot pulou a música.')

        @self.command(aliases=['r'])
        async def resume(ctx: commands.Context):
            await self.player.resume(ctx)
            self.logger.info('O bot voltou a reproduzir a música.')

        @self.command(aliases=['l'])
        async def leave(ctx: commands.Context):
            await self.player.leave(ctx)

        @self.command(aliases=['q', 'queue'])
        async def list(ctx: commands.Context):
            await self.player.list(ctx)

        self.run(self.token)
