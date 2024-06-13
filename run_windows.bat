@echo off
REM Check if virtual environment exists
IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install required packages
pip install -r requirements.txt

REM Run the main script
python code.py