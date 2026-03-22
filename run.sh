#!/bin/bash
set -e

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "Starting Kalandar at http://127.0.0.1:5000"
python3 main.py
