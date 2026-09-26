#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files into staticfiles/ for WhiteNoise
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Automatically setup production admin superuser
python manage.py setup_admin
