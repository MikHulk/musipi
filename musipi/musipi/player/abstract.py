class BasePlayer:

    def __init__(self, urls):
        self.urls = urls
        self.status = 'stopped'

    def play(self, *args, **kwargs):
        raise NotImplemented()

    def stop(self, *args, **kwargs):
        raise NotImplemented()
