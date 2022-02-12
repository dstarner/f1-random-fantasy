web: gunicorn -c fantasy_racing/config/gunicorn.py fantasy_racing.config.wsgi:application

# SPECIAL
# Release phase is responsible for migrating the database
release: ./scripts/release.sh