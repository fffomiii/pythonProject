#!/bin/sh
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
python setup.py install
f0ma  # Запуск программы
