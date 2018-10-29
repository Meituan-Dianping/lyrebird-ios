#!/usr/bin/env bash

echo "***************************"
echo "    iOS setup start   "
echo "***************************"

# create python virtual environment
python3 -m venv --clear venv

# activate virtual environment
source ./venv/bin/activate

# install from requirements.txt
pip3 install -r ./requirements.txt

# create data dir for debug
if [ ! -e "./data/" ]; then
mkdir ./data
fi

echo "***************************"
echo "   iOS setup finish   "
echo "***************************"
