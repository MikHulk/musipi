from subprocess import Popen

from .abstract import BasePlayer


class Mpg123Player(BasePlayer):

    def __init__(self, urls):
        super().__init__(urls)
        self.child = None

    def play(self, station_name):
        url = self.urls[station_name]['url']
        self.stop()
        self.child = Popen(['mpg123', url])
        self.status = 'playing'

    def stop(self):
        if self.child:
            self.child.terminate()
            self.child.wait()
            self.child = None
        self.status = 'stopped'
