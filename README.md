Animat examples
===============

Some examples using the [animat AI ecosystem](https://github.com/animatai/animatai)


Setup
=====

At least Python 3.5 is needed since `async` is used (using Python 3.6 here).

* First init `virtualenv` for Python3: `virtualenv -p python3.6 venv3` (`virutalenv` needs to be installed)
* Activate `virtualenv`: `source venv3/bin/activate`
* Install the animat ecosystem: `pip install animatai`. Upgrade with: `pip install --upgrade animatai`.
* Create a config file: `cp venv3/lib/python3.6/site-packages/animatai/config.py.template config.py`
* Having the start script here is convenient: `cp venv3/lib/python3.6/site-packages/animatai/start.sh .`


Running animat worlds
=====================

Simulations can be executed from the command line with: `./run.py <blind_dog|random_agents|random_mom_and_calf>`

It is also possible to view the worlds in a web browser:
* Start a web server: `./start.sh`
* Open `venv3/lib/python3.6/site-packages/animatai/index.html` in web browser


Development
===========

Use [Google Style Guide](https://google.github.io/styleguide/pyguide.html)
and make sure that the unit tests are maintained.

Install the development tools: `pip install -r requirements.txt`

Build (lint and run unit tests) with: `./build.sh`
