import logging
from sys import argv
import subprocess
from bottle import Bottle, run, view, redirect, abort, response, request
from musipi.player import Mpg123Player, FakePlayer
from musipi.zmq_util import ZmqPlayerProxy


STATIONS = {
    "digitalis": {
        "url": "http://ice2.somafm.com/digitalis-128-mp3",
        "name": "Digitalis",
        "id": 1,
    },
    "drone_zone": {
        "url": "http://ice4.somafm.com/dronezone-256-mp3",
        "name": "Drone Zone",
        "id": 2,
    },
    "deep_space_one": {
        "url": "http://ice4.somafm.com/deepspaceone-128-mp3",
        "name": "Deep Space One",
        "id": 3,
    },
    "indie_pop_rock": {
        "url": "http://ice2.somafm.com/indiepop-128-mp3",
        "name": "Indie Pop Rock",
        "id": 4,
    },
    "folk_fwd": {
        "url": "http://ice4.somafm.com/folkfwd-128-mp3",
        "name": "Folk Forward",
        "id": 5,
    },
}

app = Bottle()
selected_station = None

log = logging.getLogger('musipi')
logging.basicConfig(
    format='%(levelname)s %(asctime)-15s - %(name)s: %(message)s',
    level=logging.INFO)


def stop_server():
    player.stop()
    if not app.config['debug']:
        subprocess.Popen(['sudo', 'shutdown', '-t', '1', '-P'])


def add_headers(fun):
    def wrapper(*args, **kwargs):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, PUT'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Max-Age'] = '86400'
        return fun(*args, **kwargs)
    return wrapper

        
def get_station(station_id):
    try:
        return next(filter(lambda station: station['id'] == station_id,
                           STATIONS.values()))
    except StopIteration:
        return abort(404)


@app.route('/station')
@app.route('/station/<station_id:int>')
@add_headers
def get_stations(station_id=None):
    if station_id:
        log.info("get station %d" % station_id)
        return get_station(station_id)
    log.info("get stations")
    return STATIONS


@app.route('/status', ['GET'])
@add_headers
def get_status():
    log.info("get status")
    return {
        'playing': STATIONS[selected_station] if selected_station else None,
        'config': app.config,
        'player_status': player.status
    }


@app.route('/status', ['PUT', 'OPTIONS'])
@add_headers
def update_status():
    if request.method == 'OPTIONS':
        return response
    global player, selected_station
    log.info("Change player status")
    payload= request.json
    if not('playing' in payload and 'player_status' in payload):
        return abort(400)
    if payload['playing'] and payload['playing'] in STATIONS and (
            not selected_station or
            selected_station != payload['playing']):
        new_station = payload['playing']
        log.info("Station %s -> %s" % (selected_station, new_station))
        player.play(new_station)
        selected_station = new_station
    if player.status != payload['player_status']:
        new_status = payload['player_status']
        log.info("Status %s -> %s" % (player.status, new_status))
        if new_status == 'stopped':
            player.stop()
        elif new_status == 'playing' and selected_station:
            player.play(selected_station)
        else:
            return abort(400)
    return {
        'playing': STATIONS[selected_station] if selected_station else None,
        'config': app.config,
        'player_status': player.status
    }


@app.route('/stop', ['GET'])
@add_headers
def api_stop_server():
    stop_server()
    return "Stopped"


@app.route('/html')
@app.route('/html/<station:re:[A-z_]+>')
@view('main_page.tmpl')
def html_app(station=None):
    global selected_station
    if station and station != selected_station:
        player.play(station)
        selected_station = station
        return redirect("/html")
    return {"stations": STATIONS,
            "config": app.config,
            "selected_station": STATIONS[selected_station]['name']
            if selected_station else None}


@app.route('/')
def root_red():
    return redirect('/html')


@app.route('/html/player_stop')
def stop():
    stop_server()
    return redirect("/html")


def main(debug=True):
    run(app, host='0.0.0.0', port=8000, debug=debug)


if __name__ == '__main__':
    
    if len(argv) == 2 and argv[1] == 'debug':
        print("!!!! DEBUG !!!!!")
        debug = True
        log.setLevel(logging.DEBUG)
        player = ZmqPlayerProxy(FakePlayer(STATIONS))
    else:
        debug = False
        player = ZmqPlayerProxy(Mpg123Player(STATIONS))

    app.config['debug'] = debug
    main(debug)
