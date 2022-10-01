from ast import alias
import os

from discord import Activity, ActivityType, Embed, Option, Bot
from discord.ext import commands
from dotenv import load_dotenv

from src.logger import Logger
from src.lyrics.lyrics import Lyrics
from src.player.player import Player


class Bot(Bot):
    def __init__(self):
        super().__init__()
        load_dotenv()
        self.logger = Logger().get_logger()
        self.logger.info("Iniciando Bot.")
        self.token = os.getenv("TOKEN")
        self.delete_time = 10
        self.player = Player(bot=self)
        self.lyrics = Lyrics(bot=self)
        self.__version__ = "0.4.1"

        @self.event
        async def on_ready():
            self.logger.info("Bot conectado com o Discord.")
            self.loop.create_task(
                self.change_presence(
                    activity=Activity(
                        type=ActivityType.listening, name="no /play, tchama ♫"
                    )
                )
            )

        @self.command(
            description="Reproduzir música.",
            options=[
                Option(
                    str,
                    name="musica",
                    description="Nome ou link do youtube.",
                    required=True,
                )
            ],
        )
        async def play(ctx: commands.Context, play_text: str):
            self.logger.info("O bot recebeu uma solicitação de play.")
            await self.player.play(ctx, play_text)

        # DONE
        # @self.command(description="Pausar reprodutor.")
        # async def pause(ctx: commands.Context):
        #     await self.player.pause(ctx)
        #     await ctx.respond('A música foi pausada.', delete_after=3)
        #     self.logger.info('O bot pausou a música.')

        # DONE
        # @self.command(description="Pula para a próxima música.")
        # async def next(ctx: commands.Context):
        #     await self.player.next(ctx)
        #     await ctx.respond('A música foi pulada.', delete_after=3)
        #     self.logger.info('O bot pulou a música.')

        # DONE
        # @self.command(description="Continuar reprodutor.")
        # async def resume(ctx: commands.Context):
        #     await self.player.resume(ctx)
        #     await ctx.respond('A música foi resumida.', delete_after=3)
        #     self.logger.info('O bot voltou a reproduzir a música.')

        # DONE
        # @self.command(description="Força a saída do bot do canal onde está.")
        # async def leave(ctx: commands.Context):
        #     await self.player.leave(ctx)
        #     await ctx.respond('Faleu valou!', delete_after=3)
        #     self.logger.info('O bot saiu do canal de voz.')

        # @self.command(aliases=['ls', 'q', 'queue', ])
        # async def list(ctx: commands.Context):
        #     await self.delete_current_message(ctx)
        #     await self.player.list(ctx)
        #     self.logger.info('O bot listou a fila de reprodução.')

        # @self.command(aliases=['r'])
        # async def remove(ctx: commands.Context, *, idx: str):
        #     await self.delete_current_message(ctx)
        #     await self.player.remove(ctx, idx)

        # @self.command(aliases=['c'])
        # async def clear(ctx: commands.Context):
        #     await self.delete_current_message(ctx)
        #     await self.player.clear(ctx)

        # @self.command(aliases=['sf'])
        # async def shuffle(ctx: commands.Context):
        #     await self.delete_current_message(ctx)
        #     await self.player.shuffle(ctx)

        # @self.command(aliases=['ly'])
        # async def lyrics(ctx: commands.Context, *, search_text: str = None):
        #     await self.delete_current_message(ctx)
        #     await self.lyrics.search_and_send(ctx, search_text)

        # DONE
        # @self.command(description="Latência do bot.")
        # async def ping(ctx: commands.Context):
        #     lat = int(self.latency * 1000)
        #     self.logger.info(f'Latencia: {lat}ms')
        #     await ctx.respond(f"Pong! ({lat}ms)", delete_after=self.delete_time)

        self.run(self.token)

    async def delete_current_message(self, ctx: commands.Context):
        await ctx.message.delete()

    async def clear_bot_msgs_in_channel(self, ctx: commands.Context):
        channel_msgs = await ctx.channel.history(limit=100).flatten()
        bot_channel_msgs = filter(lambda msg: msg.author == self.user, channel_msgs)
        await ctx.channel.delete_messages(bot_channel_msgs)

    async def send_commands_list(self, ctx: commands.Context):
        command_list_msg_title = "🎶 **Lista de comandos**"
        commands_list_msg_description = "**-play** [-p] <nome da música> - Coloca uma música solicitada na fila\n\
                **-pause** [-ps] -  Pausa a música atual\n\
                **-resume** [-rs] - Voltar a tocar a música pausada\n\
                **-next** [-n] [-s] [-skip] - Pula para a proxima música na fila\n\
                **-list** [-ls] [-queue] [-q] - Exibi a fila de músicas a serem tocadas\n\
                **-shuffle** [-sf] - Embaralha a fila de músicas a serem tocadas\n\
                **-clear** [-c] - Limpa a fila de músicas\n\
                **-remove** [-r] <posição da música na fila>  - Remove uma música da fila\n\
                **-lyrics** [-ly] - Exibi a letra da música que está reproduzindo\n\
                **-lyrics** [-ly] <nome da música> - Exibi a letra da música solicitada\n\
                **-leave** [-l] - Me manda embora 😔\n\
                \n"
        commands_list_embed_msg = Embed(
            title=command_list_msg_title,
            description=commands_list_msg_description,
            color=0x550A8A,
        )
        commands_list_embed_msg.set_footer(text=f"Versão {self.__version__}")
        await ctx.send(embed=commands_list_embed_msg)

    async def leave(self, ctx: commands.Context):
        #await self.clear_bot_msgs_in_channel(ctx)
        #await self.send_commands_list(ctx)
        await ctx.voice_client.disconnect()
