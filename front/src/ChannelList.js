import React from 'react';
import './ChannelList.css';


function Station(props) {
    return (
        <button
          className="station-button"
          id={'station_' + props.station.id}
          onClick={() => props.onClick(props.station.id)}
        >
          {props.station.name}
        </button>
    );
}

function ChannelList(props) {
    const listItems = props.stations.map(
	(station) => {
            const isSelected = (props.selectedId === station.id);
            return (
                <div
                  key={station.id}
                  className={"station-row " + (isSelected ? "selected" : "")} >
                  <Station
                    station={station}
                    onClick={(stationId) => props.onClick(stationId)} >
                  </Station>
                </div>
            );
        });
    return <div id="station-list">{listItems}</div> ;
}

export default ChannelList;
