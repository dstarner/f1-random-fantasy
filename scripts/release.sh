#!/bin/bash
set -e

./manage.py collectstatic --no-input
./manage.py migrate
