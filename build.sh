#!/bin/bash

# Make sure we have virtualenv configured
source venv3/bin/activate

# cleanup
rm -rf docs

# run lint to check code
pylint *.py test/*.py

# Genrate docs
#pydoc -w *.py
pycco -i *.py
touch ./docs/.nojekyll

# Run the unit tests
# Run a specific unittest manually like this:
# export PYTHONPATH=test
# python -m unittest test_XXX
python -m unittest discover test
