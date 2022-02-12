#!/bin/bash
set -e

./manage.py collectstatic --no-input
./manage.py migrate

./manage.py loaddata fantasy_racing/fixtures/*.yaml