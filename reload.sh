#!/bin/sh

# ensure SIGHUP is sent to all workers
#  so they reload files
killall -HUP gunicorn
