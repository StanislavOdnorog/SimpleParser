@echo off

:: Create a virtual environment named 'venv' if it doesn't exist
if not exist venv (
    python -m venv venv
)

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Upgrade pip
python -m pip install --upgrade pip

:: Install the required packages
pip install -r requirements.txt

:: Run the scraper script
python scraper.py

:: Deactivate the virtual environment
call venv\Scripts\deactivate.bat

