import 'react-app-polyfill/stable';
import React from 'react';
import axios from 'axios';
import logo from './logo.svg';
import './App.css';
import ChannelList from './ChannelList.js';
import Control from './Control.js';


class App extends React.Component {

  constructor(props) {
    super(props);
    this.url = null;
    this.wss = null;
    this.state = {
        stations: [],
        selectedStation: null
    };
  }

  componentDidMount() {
    this.fetchServices();
  }

  initPlayer(url, ws) {
    this.url = url;
    this.wss = new WebSocket(ws);
    this.refreshStationsList();
    this.refreshPlayerStatus();
    this.wss.onopen = () => {
      console.log(`WS connected to ${ws}`);
    };
    this.wss.onmessage = evt => {
      const status = JSON.parse(evt.data);
      this.updatePlayerStatus(status);
    };
    this.wss.onerror = error => {
      this.handleError(error);
    };
    this.wss.onclose = () => {
      console.log(`WS disconnected to ${ws}`);
    };
  }

  handleError(error) {
    console.error(error);
    const refreshHandlerId = this.state.refreshHandlerId;
    window.clearInterval(refreshHandlerId);
    const state = {
      stations: [],
      selectedStation: null,
      error: error.message
    };
    this.setState(state);
  }	

  fetchServices() {
    console.log("refresh stations list");
    axios.get('/services.json')
      .then((response) =>
            this.initPlayer(response.data.player.url, response.data.status.url))
      .catch((error) => { throw error; });
  }

  updateStations(stations) {
    const selectedStation = this.state.selectedStation;
    
    let stationsList = [];
    for (let [key, value] of Object.entries(stations)){
        stationsList.push({
            keyServer: key,
            id: value.id,
            url: value.url,
            name: value.name
        });
    };
    this.setState({
      error: null,
      stations: stationsList,
      selectedStation: selectedStation
    });
  }

  refreshStationsList() {
    console.log("refresh stations list");
    axios.get(this.url + '/station')
      .then((response) => this.updateStations(response.data))
      .catch((error) => this.handleError(error));
  }

  updatePlayerStatus(status) {
    if (status.playing) {
      const stationList = this.state.stations;
      console.log("new station " + status.playing.name);
      this.setState({
        stations: stationList,
        selectedStation: status.playing
      });
    }
  }

  refreshPlayerStatus() {
    console.log("refresh player status");
    axios.get(this.url + "/status")
      .then((resp) => this.updatePlayerStatus(resp.data))
      .catch((error) => this.handleError(error));
  }

  changePlayerStatus(station) {
    console.log("change station for " + station.name);
    axios.put(this.url + "/status",
              {playing: station.keyServer,
               player_status: "playing"})
      .then((response) => this.updatePlayerStatus(response.data))
      .catch((error) => {
        console.error(error);
        this.refreshPlayerStatus();
      });
  }

  stopPlayer() {
    console.log("stop player");
    axios.get(this.url + "/stop")
      .then((resp) => this.refreshPlayerStatus())
      .catch((error) => this.handleError(error));
  }

  handleClick(stationId){
    const newStation = this.state.stations.find(
      (station) => station.id === stationId);
    this.changePlayerStatus(newStation);
  }

  render() {
    return (
      <div className="App">
        <header className="App-header">
          <img src={logo} className="App-logo" alt="logo" />
          <h1>MusiPi</h1>
          <p>{this.state.selectedStation ?
              "You're listening " + this.state.selectedStation.name :
              "stopped"}
          </p>
        </header>
        {
            this.state.error && <div className="error">{this.state.error}</div>
        }
        <ChannelList
          selectedId={this.state.selectedStation ?
                      this.state.selectedStation.id : null}
          stations={this.state.stations}
          onClick={(stationId) => this.handleClick(stationId)}
        />
        <Control
          refresh={() => this.refreshStationsList()}
          stop={() => this.stopPlayer()}
        />
      </div>
    );
  }
}

export default App;
