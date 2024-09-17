# mamba

The purpose of the tool is to **simply** downloads files, served by HTTP servers. It is done by doing a fixed-size chunking on the remote file, using the special HTTP header - [`Range`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Range), *if supported by the remote backend*.

Downloading the portions of the file and writing them on the disk operations are being handled using the [**Producer-Consumer**](https://en.wikipedia.org/wiki/Producer%E2%80%93consumer_problem) pattern

Happy Downloading!