#!/bin/bash

# run the art.py from the share and not the one in the dockerfile
# TODO remove this for public use
cd /container

while true
do
  python art.py
  sleep 3600 # one hour
done