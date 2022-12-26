from logging import exception
from src.player.song import Song
from os import listdir, makedirs, getenv
from yt_dlp import YoutubeDL
from src.logger import Logger
from re import I, match
from json import dumps, load
from datetime import date


class SongCache():

    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.logger.info('Inicializando cache.')
        self.songs_path = 'songs'
        self.cfg_path = 'cfg'
        self.cache = self.load()
        if not self.cache:
            self.cache = {}
        self.map_folder()
        self.MAX_SIZE = getenv('MAX_CACHE_SIZE', 100)

    def add_song(self, song: Song) -> None:
        # if self.queue_size() + 1 < self.MAX_SIZE:
        self.logger.info(f'Adicionando musica {song.id} ao cache.')
        self.cache[song.id] = song
        self.save()
        # else:
        #    self.logger.warn('Cache cheia.')
        #    raise NotImplemented('Fazer')

    def increment_plays(self, id: str):
        if id in self.cache:
            self.cache[id].times_played += 1
            self.cache[id].last_played = date.today().strftime("%Y-%m-%d")
        self.save()

    def load(self) -> dict:
        self.logger.info('Buscando cache em disco.')
        ret = {}
        try:
            makedirs(self.cfg_path, exist_ok=True)
            with open(f"{self.cfg_path}/cache.json", 'r') as data:
                self.logger.info('Arquivo de cache encontrado, carregando.')
                tmp = load(data)
                for i in tmp:
                    ret[tmp[i]['id']] = Song(tmp[i]['id'], tmp[i])
                self.logger.info('Cache carregado com sucesso.')
            return ret
        except FileNotFoundError as e:
            self.logger.warn(f'Arquivo de cache não encontrado [{e}]')
            return None
        except Exception as e:
            self.logger.error(f'Erro ao carregar arquivo de cache [{e}]')
            return None

    def save(self) -> None:
        try:
            makedirs(self.cfg_path, exist_ok=True)
            with open(f"{self.cfg_path}/cache.json", 'w') as out:
                out.write(self.to_json())
            self.logger.info('Cache salvo em disco.')
        except Exception as e:
            self.logger.critical(f'Erro ao salvar arquivo de cache [{e}]')

    def get_song(self, id: str) -> Song:
        song = self.cache.get(id)
        return song

    def queue_size(self) -> int:
        return len(self.cache)

    def to_json(self) -> str:
        output = {}
        for song in self.cache:
            tmp = self.cache[song].to_dict()
            output[tmp['id']] = tmp
        return dumps(output, indent=4)

    def map_folder(self) -> None:
        self.logger.info('Mapping songs from folder')
        f = []

        makedirs(self.songs_path, exist_ok=True)
        files = listdir(self.songs_path)
        for f in files:
            id = str(match(r'(.*)\..*', f).group(1))
            url = 'https://www.youtube.com/watch?v=' + id
            if id not in self.cache:
                self.logger.info(
                    f'Musica {id} nao consta no cache, baixando informacoes.')
                yt = YoutubeDL()
                song_info = yt.extract_info(url, download=False)
                song_info[
                    'path'] = f'{self.songs_path}/{song_info["id"]}.{song_info["ext"]}'
                song_info['url'] = url

                new_song = Song(song_info['id'], song_info)

                self.cache[song_info['id']] = new_song
                self.logger.info(f'Musica {id} adicionada no cache')
        self.save()
