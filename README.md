This is a simple stream selector for [mpg123](https://www.mpg123.de/) with a web interface for an rpi3.

It's not production ready. Lakes lot of thing: authentication, ssl, etc... It was helpful on my local LAN, but definitely not something to put on the internet. (Or maybe for a kind of social experience, I don't know).

Basically it allows to select an audio stream from a pre-selected list and then play it with mpg123.

There are 4 modules:
- musipi the python back-end written with bottle,
- the react front-end (surprisingly, called front),
- musipi-socket, which is a ws server. It listens to a zmq channel from the backend and update client's browsers when the previous selected stream was changed for a new one.
- stream-guard, manages mpg123 process and relaunches it when it is freezed (after a connection loss, by instance),
