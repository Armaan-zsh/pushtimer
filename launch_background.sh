#!/bin/bash
cd /home/spacecadet/Documents/github-all/pushtimer
source venv/bin/activate
nohup python main.py > /dev/null 2>&1 &
