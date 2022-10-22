$(function () {
  "use strict";
  // for better performance - to avoid searching in DOM
  var statusElem = $('#status');
  // if user is running mozilla then use it's built-in WebSocket
  window.WebSocket = window.WebSocket || window.MozWebSocket;
  // if browser doesn't support WebSocket, just show
  // some notification and exit
  if (!window.WebSocket) {
    statusElem.html($('<p>',
      { text:'Sorry, but your browser doesn\'t support WebSocket.'}
    ));
    return;
  }
  // open connection
  var connection = new WebSocket('ws://192.168.23.100:8080');

  connection.onopen = function () {
    statusElem.text('Connected');
  };
  connection.onerror = function (error) {
    // just in there were some problems with connection...
    statusElem.html($('<p>', {
      text: 'Sorry, but there\'s some problem with your '
         + 'connection or the server is down.'
    }));
  };
  // most important part - incoming messages
  connection.onmessage = function (message) {
    // try to parse JSON message. Because we know that the server
    // always returns JSON this should work without any problem but
    // we should make sure that the massage is not chunked or
    // otherwise damaged.
    try {
      var resp = JSON.parse(message.data);
    } catch (e) {
      console.log('Invalid JSON: ', message.data);
      return;
    }
    console.log(resp);
    addMessage(resp.playing, resp.player_status, resp.config);
  };

  /**
   * This method is optional. If the server wasn't able to
   * respond to the in 3 seconds then show some error message 
   * to notify the user that something is wrong.
   */
  setInterval(function() {
    if (connection.readyState !== 1) {
      statusElem.text('Error');
    }
  }, 3000);
  
  /**
   * Add message to the chat window
   */
  function addMessage(playing, status, color, ) {
    statusElem.empty();
    statusElem.append('<p><span class="label">Status:</span> ' + status + '</p>' +
                      '<p><span class="label">Playing:</span> ' + playing.name + '</p>');
  }
});
