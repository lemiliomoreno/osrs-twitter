#!/bin/bash

source venv_osrs_manager/bin/activate

export TWITTER_API_CONSUMER_KEY="your CONSUMER_KEY"
export TWITTER_API_CONSUMER_SECRET="your CONSUMER_SECRET"
export TWITTER_API_ACCESS_KEY="your ACCESS_KEY"
export TWITTER_API_ACCESS_SECRET="your ACCESS_SECRET"

export TWITTER_API_ACCOUNT_ID="your ACCOUNT_ID"

python /home/osrs_manager/osrs_ge/get_dm.py >> osrs_manager__logs.txt
