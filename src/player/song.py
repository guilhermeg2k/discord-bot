from datetime import date


class Song():
    def __init__(self, id: str, info: dict) -> None:
        self.id = id
        self.from_dict(info)

    def to_dict(self) -> dict:
        output = {}
        output['id'] = self.id
        output['path'] = self.path
        output['title'] = self.title
        output['duration'] = self.duration
        output['thumb'] = self.thumb
        output['url'] = self.url
        output['added_date'] = self.added_date
        output['last_played'] = self.last_played
        output['times_played'] = self.times_played
        output['track'] = self.track
        output['artist'] = self.artist
        return output

    def from_dict(self, info: dict) -> None:
        if 'thumb' in info:
            thumbnail = info['thumb']
        else:
            for thumb in info['thumbnails']:  # TODO ORDER BY PREFERENCE, POP FIRST
                if thumb['preference'] == 0:
                    thumbnail = thumb['url']

        if 'requester' in info:
            self.requester = info['requester']
        else:
            self.requester = None

        if 'added_date' in info:
            self.added_date = info['added_date']
        else:
            self.added_date = date.today().strftime("%Y-%m-%d")

        if 'last_played' in info:
            self.last_played = info['last_played']
        else:
            self.last_played = date.today().strftime("%Y-%m-%d")

        if 'times_played' in info:
            self.times_played = info['times_played']
        else:
            self.times_played = 0

        self.url = info.get('url')
        self.path = info.get('path')
        self.title = info.get('title')
        self.duration = info.get('duration')
        self.thumb = thumbnail
        self.track = info.get('track')
        self.artist = info.get('artist')

        self.lyrics = None
