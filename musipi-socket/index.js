const WebSocket = require('ws');
const http = require('http');
const util = require('util');
var zmq = require('zeromq');


const MUSIPI_URL = process.env.MUSIPI_URL || 'localhost:8000';
const ZMQ_SOCKET = process.env.MUSIPI_ZMQ_SOCKET || 'tcp://localhost:5556';
let [host, port] = MUSIPI_URL.split(':');

const musipiReqOptions = {
  host,
  port: port ? port : 80,
  path: '/status',
  method: 'GET',
  headers: {
    'Accept': 'application/json'
  }
};

var clientId = 0;

const wss = new WebSocket.Server({
  port: process.env.MUSIPI_PORT || 8080,
  clientTracking: false});
var clients = {};

function receptStatus(res) {
  var body = '';
  res.on('data', (chunk) => { body = body + chunk; });
  res.on('end', () => {
    let raw = body;
    let resp = JSON.parse(body);
    console.log(util.inspect(resp));
    Object.entries(clients).forEach(([ip, ws]) => {
      console.log(`send status to ${ip}`);
      ws.send(body);
    });
  });
}

function inquireStatus(url) {
  console.log('Inquire Status');
  let req = http.request(musipiReqOptions, receptStatus);
  req.end();
}

wss.on('connection', (ws, req) => {
  clientId = (clientId + 1) % 2000;
  const ip = req.connection.remoteAddress + '_' + clientId;
  console.log(`new client ${ip}`);
  clients[ip] = ws;
  ws.on('close', (code, reason) => {
    delete clients[ip];
    console.log(`client ${ip} is going out for ${reason}`);
    console.log(util.inspect(Object.keys(clients)));
  });
});

inquireStatus(MUSIPI_URL);
console.log("Server start", wss);

(async function () {
  const sock = new zmq.Subscriber;

  sock.connect(ZMQ_SOCKET);
  sock.subscribe('');
  console.log("Waiting for status");
  
  for await (const msg of sock) {
    console.log("received a message");
    let status = JSON.parse(msg);
    console.log(status);
    if (status.type == 'new_status') {
      console.log("get status");
      await inquireStatus(MUSIPI_URL);
    }
  }
})().catch((e) => console.error(e));
