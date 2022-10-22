var zmq = require('zeromq');

(async function () {
  const sock = new zmq.Subscriber;

  sock.connect("tcp://localhost:5556");
  sock.subscribe('');
  console.log("Waiting for status");
  
  for await (const msg of sock) {
    console.log("received a message");
    let status = await JSON.parse(msg);
    console.log(status);
  }
})().catch((e) => console.error(e));

