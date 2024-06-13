@echo off
REM Check if virtual environment exists
IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install required packages
pip install -r requirements2.txt
pip install pygame==2.5.2

REM Run the main script
python code.py
