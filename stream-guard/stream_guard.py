import urllib.request
import json
import os
import re
import sys
import types
import traceback
from time import sleep

MUSIPI_URL = os.environ.get('MUSIPI_URL', 'http://localhost:8000')
IT_DELAY = os.environ.get('STREAMGUARD_IT_DELAY', 10)


############################## FSM ############################################


class Symbol(type):

    def __call__(self):
        raise TypeError("Symbols are not callable")

    def __repr__(self):
        return self.__name__


class Default(metaclass=Symbol):
    pass


class FSMachine:
    """>>> from stream_guard import FSMachine, Default
    >>> states = [
    ...     {'process': lambda val, res: [(val or 0) + 1] * 2,
    ...      'transitions': {Default: 1}},
    ...     {'process': lambda val, res: (val, val > 5),
    ...      'transitions': {True: None, False: 0}}]
    >>> machine = FSMachine(states)
    >>> machine.current_state
    {...}
    >>> machine(4)
    6
    >>> machine.value
    6
    >>> type(machine.current_state)
    <class 'NoneType'>
    >>>
    """

    def __init__(self, states, debug=False):
        self.current_state = states[0]
        self.states = states
        self.value = None
        self.result = None
        self.debug = debug

    def __call__(self, start_value=None):
        self.value = self.value or start_value

        while self.current_state:
            f = self.current_state['process']
            (self.value, self.result) = f(self.value, self.result)
            if self.debug:
                print("new value: %s" % self.value)
                print("new result: %s" % self.result)

            transitions = self.current_state.get('transitions', {})
            transition = transitions.get(self.result, None)
            if transition is None:
                transition = transitions.get(Default, None)
            if self.debug:
                print("transition: %s" % transition)

            if transition is not None:
                self.current_state = self.states[transition]
            else:
                self.current_state = None
            if self.debug:
                print("new state: %s" % self.current_state)

        if self.debug:
            print("stop")

        return self.value


############################# Utils ###########################################


def get_status(musipi_url: str):
    with urllib.request.urlopen("%s/status" % musipi_url) as f:
        return json.loads(f.read().decode())

def get_stations(musipi_url: str):
    with urllib.request.urlopen("%s/station" % musipi_url) as f:
        return json.loads(f.read().decode())

def get_station_id(playing: dict, stations: dict):
    return next(station_id for station_id, data in stations.items()
                if data['id'] == playing['id'])

def from_cmd_output(cmd):
    with os.popen(cmd) as f:
        return f.read()

def parse_netstat(output):
    goal = re.finditer(r'^tcp +(\d+).* +(\d+)/mpg123 *$', output, re.M)
    if goal:
        return [{ "buffer": int(item.group(1)), "pid": item.group(2) } for
                item in goal]

def parse_systemd(output):
    goal = re.search(r'^.*─ *(\d{1,5}) mpg123.*$', output, re.M)
    if goal:
        return goal.group(1)

def change_station(musipi_url: str, station_id):
    req = urllib.request.Request("%s/status" % musipi_url,
                                 data=json.dumps({'player_status': "playing",
                                                  'playing': station_id}).encode(),
                                 headers={'content-type': 'application/json'},
                                 method='PUT')
    with urllib.request.urlopen(req) as f:
        return json.loads(f.read().decode())


############# STATES ##########################################################

def get_player_pid(value, result):
    sd_out = from_cmd_output('systemctl status soma')
    pid = parse_systemd(sd_out)
    if pid:
        return pid, None
    else:
        return None, 'no_pid'

def get_stream_status(pid, result):
    ns_out = from_cmd_output('netstat -tnp')
    streams = parse_netstat(ns_out)
    try:
        stream = next(stream['buffer'] for stream in streams
                      if stream['pid'] == pid)
    except StopIteration:
        return None, False
    is_ok = stream > 0
    if not is_ok:
        print("stream is lost")
    return stream, is_ok

def wait(_, __):
    sleep(IT_DELAY)
    return None, None

def get_station(value, result):
    status = get_status(MUSIPI_URL)
    if status["player_status"] != 'playing':
        return None, 'no_play'
    stations = get_stations(MUSIPI_URL)
    return get_station_id(status['playing'], stations), None

def restart_station(station_id, result):
    print("restart station")
    stations = get_stations(MUSIPI_URL)
    other_id = next(station_id for station_id, data in stations.items()
                    if data['id'] != station_id)
    change_station(MUSIPI_URL, other_id)
    change_station(MUSIPI_URL, station_id)
    return station_id, station_id


######################## Main function ########################################

def main(debug=False):
    states = [
        {'process': get_player_pid,
         'transitions': {Default: 1, 'no_pid': 3}},
        {'process': get_stream_status,
         'transitions': {True: 2, False: 3}},
        {'process': wait,
         'transitions': {Default: 0}},
        {'process': get_station,
         'transitions': {Default: 4, 'no_play': 3}},
        {'process': restart_station,
         'transitions': {Default: 2}}]
    fsm = FSMachine(states, debug)
    fsm()

def test():
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
    NS_OUTPUT = (
        "Connexions Internet actives (sans serveurs)\n"
        "Proto Recv-Q Send-Q Adresse locale          Adresse distante        "
        "Etat        PID/Program name    \n"
        "tcp        0    188 192.168.1.3:ssh         192.168.1.2:38838       "
        "ESTABLISHED 5894/sshd: pi [priv \n"
        "tcp   257272      0 192.168.23.100:33430    ice2.somafm.com:http    "
        "ESTABLISHED 6102/mpg123         \n"
        "tcp   0      0 192.168.23.100:33430    ice2.somafm.com:http    "
        "ESTABLISHED 6103/mpg123         \n"
        "tcp        0      0 192.168.1.3:ssh         192.168.1.2:59232       "
        "ESTABLISHED 2125/sshd: pi [priv \n"
        "tcp        0      0 192.168.1.3:ssh         192.168.1.2:59230       "
        "ESTABLISHED 2106/sshd: pi [priv \n")
    SD_OUTPUT = (
        "● soma.service - Early soma launcher\n"
        "   Loaded: loaded (/etc/systemd/system/soma.service; enabled; vendor "
        "preset: enabled)\n"
        "   Active: active (running) since Wed 2020-03-04 08:01:23 CET; 4 days ago\n"
        " Main PID: 442 (soma.sh)\n"
        "    Tasks: 4 (limit: 4915)\n"
        "CGroup: /system.slice/soma.service\n"
        "        ├─  442 /bin/sh /home/pi/soma.sh\n"
        "        ├─  722 python3 /home/pi/musipi/musipi/server.py\n"
        "        └─31948 mpg123 http://ice4.somafm.com/deepspaceone-128-mp3\n"
        "mars 08 21:18:32 raspberrypi soma.sh[442]: INFO 2020-03-08 21:18:32,522 - "
        "musipi: get stations\n"
        'mars 08 21:18:44 raspberrypi soma.sh[442]: 192.168.1.2 - - '
        '[08/Mar/2020 21:18:32] "GET /station HTTP/1.1" \n'
        'mars 08 21:18:44 raspberrypi soma.sh[442]: INFO 2020-03-08 21:18:44,099'
        '- musipi: get status\n'
        'mars 08 21:18:44 raspberrypi soma.sh[442]: 192.168.1.2 - - '
        '[08/Mar/2020 21:18:44] "GET /status HTTP/1.1" 2\n'
        'mars 08 21:18:44 raspberrypi soma.sh[442]: INFO 2020-03-08 '
        '21:18:44,110 - musipi: get stations\n'
        'mars 08 21:19:04 raspberrypi soma.sh[442]: 192.168.1.2 - - '
        '[08/Mar/2020 21:18:44] "GET /station HTTP/1.1" \n')

    status = get_status(MUSIPI_URL)
    stations = get_stations(MUSIPI_URL)
    on_air = get_station_id(status['playing'], stations)

    print("station id is %s" % on_air)
    print(from_cmd_output('echo "ok it works"'))
    print(parse_netstat(NS_OUTPUT))
    states = [
        {'process': lambda val, res: [(val or 0) + 1] * 2,
         'transitions': {Default: 1}},
        {'process': lambda val, res: (val, val > 5),
         'transitions': {True: None, False: 0}}]
    machine = FSMachine(states, debug=True)
    machine()
    print(parse_systemd(SD_OUTPUT))
    print(change_station(MUSIPI_URL, 'digitalis'))
    print(change_station(MUSIPI_URL, '9128'))


if __name__ == "__main__":
    if sys.argv[1] == 'test':
        test()
    elif sys.argv[1] == 'run':
        main(debug=len(sys.argv) > 2 and sys.argv[2] == 'debug')
    else:
        print("Fuck you...")
