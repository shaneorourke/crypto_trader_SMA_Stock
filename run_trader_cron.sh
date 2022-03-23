#!/bin/bash
. /home/pi/.bashrc

PATH=$(dirname "$0")

cd $PATH &&
source trader/bin/activate &&
python trader.py