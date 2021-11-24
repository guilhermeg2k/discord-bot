from datetime import date


class Song():
    def __init__(self, id: str, path: str, title: str, duration: float, requester: str, url: str, thumb: str) -> None:
        self.id = id
        self.path = path
        self.title = title
        self.duration = duration
        self.thumb = thumb
        self.requester = requester
        self.url = url
        self.added_date = date.today()
        self.last_played = date.today()
        self.times_played = 0
