from .abstract import BasePlayer


class FakePlayer(BasePlayer):
    
    def play(self, station_name):
        print("let's play %s " % station_name)
        self.status = 'playing'

    def stop(self, *args, **kwargs):
        print("stop")
        self.status = 'stopped'
