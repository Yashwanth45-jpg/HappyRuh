
import sys
import os

# Add the src directory to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db_logger.db import create_tables

if __name__ == "__main__":
    print("Attempting to create database tables from schema script...")
    create_tables()
    print("Schema script finished.")
