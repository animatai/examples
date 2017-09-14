Animat examples
===============

Some examples using the [animat AI ecosystem](https://github.com/animatai/ecosystem)


Setup
=====

At least Python 3.5 is needed since `async` is used (using Python 3.6 here).

* First init `virtualenv` for Python3: `virtualenv -p python3.6 venv3` (`virutalenv` needs to be installed)
* Activate `virtualenv`: `source venv3/bin/activate`
* Install the animat ecosystem: `pip install animats`.


Development
===========

Use [Google Style Guide](https://google.github.io/styleguide/pyguide.html)
and make sure that the unit tests are maintained.

Install the development tools: `pip install -r requirements.txt`

Build (lint and run unit tests) with: `./build.sh`
