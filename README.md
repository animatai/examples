Animat examples
===============

Some examples using the [animat AI ecosystem](https://github.com/animatai/ecosystem)


Setup
=====

At least Python 3.5 is needed since `async` is used (using Python 3.6 here).

* First init `virtualenv` for Python3: `virtualenv -p python3.6 venv3` (`virutalenv` needs to be installed)
* Activate `virtualenv`: `source venv3/bin/activate`
* Install the animat ecosystem: `pip install animats`.
* Create a config file: `cp venv3/lib/python3.6/site-packages/ecosystem/config.py.template config.py`
* Having the start script here is convenient: `cp venv3/lib/python3.6/site-packages/ecosystem/start.sh .`


Running animat worlds
=====================

Start a web server: `./start.sh`

Open `venv3/lib/python3.6/site-packages/ecosystem/index.html` in web browser


Development
===========

Use [Google Style Guide](https://google.github.io/styleguide/pyguide.html)
and make sure that the unit tests are maintained.

Install the development tools: `pip install -r requirements.txt`

Build (lint and run unit tests) with: `./build.sh`
