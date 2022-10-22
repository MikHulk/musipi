import React from 'react';
import './Control.css';

function Control(props) {
    return (
        <div id="control">
          <button id="refresh-button"
                  className="control-button"
                  onClick={() => props.refresh()}>
            refresh
          </button>
          <button id="stop-button"
                  className="control-button"
                  onClick={() => props.stop()}>
            stop
          </button>
        </div>);
}

export default Control;
