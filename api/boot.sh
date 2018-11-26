#!/bin/sh

exec gunicorn --worker-class eventlet -w 1 --log-level debug --bind 0.0.0.0:5000 app:app