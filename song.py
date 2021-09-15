
class Song():
    def __init__(self, song_info: dict) -> None:
        self.id = song_info['id']
        self.path = f'{song_info["id"]}.{song_info["ext"]}'
        self.title = song_info['title']
        self.duration = song_info['duration']

    def set_folder(self, folder: str ) -> None:
        self.path = folder + '\\' + self.path 