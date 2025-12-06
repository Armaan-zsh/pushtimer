#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py 2>&1 | tee -a ~/.local/share/pushtimer/app.log
