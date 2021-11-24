
class Song():
    def __init__(self, id: str, path: str, title: str, duration: float, requester: str) -> None:
        self.id = id
        self.path = path
        self.title = title
        self.duration = duration
        self.requester = requester

    def set_requester(self, requester: str) -> None:
        self.requester = requester