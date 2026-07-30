#!/bin/bash
# Crontab setup script for periodic news alert generation
# Runs every 24 hours (or customizable interval)

PYTHON_PATH=$(which python3)
SCRIPT_PATH="$(pwd)/news_fetcher.py"
LOG_PATH="$(pwd)/news_alert.log"

# Example Crontab entry (Runs daily at 08:00 AM)
# 0 8 * * * cd $(pwd) && $PYTHON_PATH $SCRIPT_PATH >> $LOG_PATH 2>&1

# Add to crontab via command line:
(crontab -l 2>/dev/null; echo "0 8 * * * cd $(pwd) && $PYTHON_PATH $SCRIPT_PATH >> $LOG_PATH 2>&1") | crontab -

echo "Crontab job installed successfully! Current crontab:"
crontab -l
