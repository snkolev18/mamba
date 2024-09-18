# mamba

### Intro

The purpose of the tool is to **simply** downloads files, served by HTTP servers. It is done by doing a fixed-size chunking on the remote file, using the special HTTP header - [`Range`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Range), *if supported by the remote backend*.

Downloading the portions of the file and writing them on the disk operations are being handled using the [**Producer-Consumer**](https://en.wikipedia.org/wiki/Producer%E2%80%93consumer_problem) pattern

### Setup

```shell
git clone https://github.com/snkolev18/mamba
cd mamba
python3 -m venv ./venv
. ./venv/bin/activate
pip3 install -r requirements.txt
```

You can also symlink once you complete the installation:
```shell
chmod +x ./mamba
sudo ln -s $(pwd)/mamba /usr/bin/mamba
```

Happy Downloading!