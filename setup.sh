#!bin/bash

chmod +x run_trader.sh &&
python3 -m venv trader &&
source trader/bin/activate &&
pip install -r requirements.txt &&
python setup.py &&
deactivate