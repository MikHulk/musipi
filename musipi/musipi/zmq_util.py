from os import environ
from logging import getLogger
import zmq
from musipi.player.abstract import BasePlayer

log = getLogger('musipi.zmq')


class ZmqPlayerProxy(BasePlayer):
    
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(environ.get('ZMQ_BOUND', 'tcp://*:5556'))

    def __init__(self, real_player):
        self.real_player = real_player

    @property
    def status(self):
        msg = 'get status from real player'
        log.debug(msg)
        self.socket.send_json({ 'type': 'message', 'message': msg })
        return self.real_player.status

    @property
    def station(self):
        msg = 'get station from real player'
        log.debug(msg)
        self.socket.send_json({ 'type': 'message', 'message': msg })
        return self.real_player.station

    def play(self, *args, **kwargs):
        log.debug("send play to real player")
        log.debug(args)
        log.debug(kwargs)
        self.socket.send_json({'type': 'new_status',
                               'event': 'new_play',
                               'args': list(args),
                               'kwargs': kwargs})
        self.real_player.play(*args, **kwargs)

    def stop(self, *args, **kwargs):
        log.debug("send stop to real player")
        log.debug(args)
        log.debug(kwargs)
        self.socket.send_json({'type': 'new_status',
                               'event': 'player_stop',
                               'args': list(args),
                               'kwargs': kwargs})
        self.real_player.stop(*args, **kwargs)
