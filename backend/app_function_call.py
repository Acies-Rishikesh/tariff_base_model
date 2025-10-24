import subprocess
import sys
from data_cleaner import run_data_cleaning

def clean_data():
    """Function to be called for data cleaning."""
    run_data_cleaning()

def run_streamlit_app():
    """Function to run the Streamlit application."""
    # Run streamlit with the ui/streamlit.py file
    subprocess.run([sys.executable, "-m", "streamlit", "run", "ui/streamlit.py"], check=True)
