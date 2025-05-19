import os
import shutil
from typing import List, Dict, Any

def ensure_temp_directory():
    """Ensure the temporary directory exists"""
    temp_dir = "./temp"
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def clean_temp_directory():
    """Clean the temporary directory"""
    temp_dir = "./temp"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)