#!/usr/bin/env bash

# source venv/bin/activate

# until pypy3 runScrape.py raw; do
until python3 runScrape.py raw noreset; do
    echo "Server 'pypy3 runScrape.py raw' crashed with exit code $?.  Respawning.." >&2
    sleep 1
done