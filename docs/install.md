# Installation

There are three ways to install *upcheck* on your machine. Via a manual binary download, an install script, or installation of the python package.

## Binaries

To install `upcheck`, download the appropriate binary from one of the links below, and set the downloaded file to be executable (``chmod +x upcheck``):

  - [Linux](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/linux-gnu/upcheck)
  - [Windows](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/windows/upcheck.exe) -- not tested at all
  - [Mac OS X](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/darwin/upcheck) -- not available (yet)

## Install script  

Alternatively, use the 'curly' install script for `upcheck`:

    > curl https://gitlab.com/makkus/upcheck/-/raw/develop/scripts/install/upcheck.sh | bash
    - downloaded upcheck: /home/markus/.local/share/frkl/bin/upcheck  
    - added init section to: /home/markus/.profile
    > source ~/.profile

## Python package

The python package is currently not available on [pypi](https://pypi.org), so you need to specify the ``--extra-url`` parameter for your pip command. If you chooose this install method, I assume you know how to install Python packages manually, which is why I only show you an example way of getting *upcheck* onto your machine:

```
> python3 -m venv ~/.venvs/upcheck
> source ~/.venvs/upcheck/bin/activate
> pip install --extra-index-url https://pkgs.frkl.io/frkl/dev upcheck
Looking in indexes: https://pypi.org/simple, https://pkgs.frkl.io/frkl/dev
Collecting upcheck
  Downloading http://pkgs.frkl.io/frkl/dev/%2Bf/ee3/f57bd91a076f9/upcheck-0.1.dev24%2Bgd3c4447-py2.py3-none-any.whl (28 kB)
...
...
...
Successfully installed aiokafka-0.6.0 aiopg-1.0.0 ... ... ...
>

```  

# Update

The binary can update itself. To do that, issue:

    > upcheck self update
