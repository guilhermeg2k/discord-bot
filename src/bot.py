import traceback
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
        self.delete_time = 30
        self.player = Player(bot=self)
        self.lyrics = Lyrics(bot=self)
        self.__version__ = "0.5.0"

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
            try:
                await self.player.play(ctx, play_text)
            except Exception as err:
                error = str(traceback.format_exc())
                self.logger.error(error)
                await self.send_exception(error, command="play")
                embed_msg = Embed(
                    title="ERRO",
                    description="Desculpe,\nTive um erro interno.",
                    color=0xFF0000,
                )
                await ctx.respond(embed=embed_msg, delete_after=5)

        @self.command(description="Pausar reprodutor.")
        async def pause(ctx: commands.Context):
            try:
                await self.player.pause(ctx)
                await ctx.respond(
                    "A música foi pausada.", delete_after=self.delete_time
                )
                self.logger.info("O bot pausou a música.")
            except Exception as err:
                error = str(traceback.format_exc())
                self.logger.error(error)
                await self.send_exception(error, command="pause")
                embed_msg = Embed(
                    title="ERRO",
                    description="Desculpe,\nTive um erro interno.",
                    color=0xFF0000,
                )
                await ctx.respond(embed=embed_msg, delete_after=5)

        @self.command(description="Pula para a próxima música.")
        async def next(ctx: commands.Context):
            try:
                await self.player.next(ctx)
                await ctx.respond("A música foi pulada.", delete_after=self.delete_time)
                self.logger.info("O bot pulou a música.")
            except Exception as err:
                error = str(traceback.format_exc())
                self.logger.error(error)
                await self.send_exception(error, command="next")
                embed_msg = Embed(
                    title="ERRO",
                    description="Desculpe,\nTive um erro interno.",
                    color=0xFF0000,
                )
                await ctx.respond(embed=embed_msg, delete_after=5)

        @self.command(description="Continuar reprodutor.")
        async def resume(ctx: commands.Context):
            try:
                await self.player.resume(ctx)
                await ctx.respond(
                    "A música foi resumida.", delete_after=self.delete_time
                )
                self.logger.info("O bot voltou a reproduzir a música.")
            except Exception as err:
                error = str(traceback.format_exc())
                self.logger.error(error)
                await self.send_exception(error, command="resume")
                embed_msg = Embed(
                    title="ERRO",
                    description="Desculpe,\nTive um erro interno.",
                    color=0xFF0000,
                )
                await ctx.respond(embed=embed_msg, delete_after=5)

        @self.command(description="Força a saída do bot do canal onde está.")
        async def leave(ctx: commands.Context):
            try:
                await self.player.leave(ctx)
                await ctx.respond("Faleu valou!", delete_after=self.delete_time)
                self.logger.info("O bot saiu do canal de voz.")
            except Exception as err:
                error = str(traceback.format_exc())
                self.logger.error(error)
                await self.send_exception(error, command="leave")
                embed_msg = Embed(
                    title="ERRO",
                    description="Desculpe,\nTive um erro interno.",
                    color=0xFF0000,
                )
                await ctx.respond(embed=embed_msg, delete_after=5)

        @self.command(description="Mostra a fila de reprodução.")
        async def list(ctx: commands.Context):
            try:
                await self.player.list(ctx)
                self.logger.info("O bot listou a fila de reprodução.")
            except Exception as err:
                error = str(traceback.format_exc())
                self.logger.error(error)
                await self.send_exception(error, command="list")
                embed_msg = Embed(
                    title="ERRO",
                    description="Desculpe,\nTive um erro interno.",
                    color=0xFF0000,
                )
                await ctx.respond(embed=embed_msg, delete_after=5)

        @self.command(
            description="Remover música da fila.",
            options=[
                Option(
                    int,
                    name="posicao",
                    description="Posição da música na fila.",
                    required=True,
                )
            ],
        )
        async def remove(ctx: commands.Context, *, idx: int):
            try:
                await self.player.remove(ctx, idx)
            except Exception as err:
                error = str(traceback.format_exc())
                self.logger.error(error)
                await self.send_exception(error, command="remove")
                embed_msg = Embed(
                    title="ERRO",
                    description="Desculpe,\nTive um erro interno.",
                    color=0xFF0000,
                )
                await ctx.respond(embed=embed_msg, delete_after=5)

        @self.command(description="Limpa a fila de reprodução.")
        async def clear(ctx: commands.Context):
            try:
                rs = await self.player.clear(ctx)
                if rs:
                    await ctx.respond("Fila esvaziada!", delete_after=self.delete_time)
                else:
                    embed_msg = Embed(
                        title="Fila vazia",
                        description="Adicione músicas :)",
                        color=0xEB2828,
                    )
                    await ctx.respond(embed=embed_msg, delete_after=self.delete_time)
            except Exception as err:
                error = str(traceback.format_exc())
                self.logger.error(error)
                await self.send_exception(error, command="clear")
                embed_msg = Embed(
                    title="ERRO",
                    description="Desculpe,\nTive um erro interno.",
                    color=0xFF0000,
                )
                await ctx.respond(embed=embed_msg, delete_after=5)

        @self.command(description="Embaralha a fila de reprodução.")
        async def shuffle(ctx: commands.Context):
            try:
                await self.player.shuffle(ctx)
            except Exception as err:
                error = str(traceback.format_exc())
                self.logger.error(error)
                await self.send_exception(error, command="shuffle")
                embed_msg = Embed(
                    title="ERRO",
                    description="Desculpe,\nTive um erro interno.",
                    color=0xFF0000,
                )
                await ctx.respond(embed=embed_msg, delete_after=5)

        @self.command(
            description="Busca a letra da música. Como padrão utiliza a música que está sendo reproduzida caso haja.",
            options=[
                Option(
                    str,
                    name="musica",
                    description="Informar nome da música manualmente.",
                    required=False,
                )
            ],
        )
        async def lyrics(ctx: commands.Context, search_text: str = None):
            try:
                await self.lyrics.search_and_send(ctx, search_text)
            except Exception as err:
                error = str(traceback.format_exc())
                self.logger.error(error)
                await self.send_exception(error, command="lyrics")
                embed_msg = Embed(
                    title="ERRO",
                    description="Desculpe,\nTive um erro interno.",
                    color=0xFF0000,
                )
                await ctx.respond(embed=embed_msg, delete_after=5)

        @self.command(description="Latência do bot.")
        async def ping(ctx: commands.Context):
            try:
                lat = int(self.latency * 1000)
                self.logger.info(f"Latencia: {lat}ms")
                await ctx.respond(f"Pong! ({lat}ms)", delete_after=self.delete_time)
            except Exception as err:
                error = str(traceback.format_exc())
                self.logger.error(error)
                await self.send_exception(error, command="ping")
                embed_msg = Embed(
                    title="ERRO",
                    description="Desculpe,\nTive um erro interno.",
                    color=0xFF0000,
                )
                await ctx.respond(embed=embed_msg, delete_after=5)

        self.run(self.token)

    async def send_commands_list(self, ctx: commands.Context):
        command_list_msg_title = "🎶 **Lista de comandos**"
        commands_list_msg_description = "**/play** <nome da música> - Coloca uma música solicitada na fila\n\
                **/pause** -  Pausa a música atual\n\
                **/resume** - Voltar a tocar a música pausada\n\
                **/next** - Pula para a proxima música na fila\n\
                **/list** - Exibi a fila de músicas a serem tocadas\n\
                **/shuffle** - Embaralha a fila de músicas a serem tocadas\n\
                **/clear** - Limpa a fila de músicas\n\
                **/remove** <posição da música na fila>  - Remove uma música da fila\n\
                **/lyrics** - Exibi a letra da música que está reproduzindo\n\
                **/lyrics** <nome da música> - Exibi a letra da música solicitada\n\
                **/leave** - Me manda embora 😔\n\
                \n"
        commands_list_embed_msg = Embed(
            title=command_list_msg_title,
            description=commands_list_msg_description,
            color=0x550A8A,
        )
        commands_list_embed_msg.set_footer(text=f"Versão {self.__version__}")
        await ctx.send(embed=commands_list_embed_msg)

    async def send_exception(self, exception: str, command: str = None) -> None:
        debug_guild = int(os.getenv("DEBUG_GUILD"))
        debug_channel = int(os.getenv("DEBUG_CHANNEL"))
        if not (debug_guild and debug_channel):
            self.logger.error("Falha nos parametros de debug")
            return
        out = self.get_guild(debug_guild).get_channel(debug_channel)
        if command:
            emb_title = f"Exception on: {command}"
        else:
            emb_title = f"Exception"
        exeption_embed_msg = Embed(
            title=emb_title,
            description=exception,
            color=0xFF0000,
        )
        await out.send(embed=exeption_embed_msg)
