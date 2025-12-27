#!/usr/bin/env bash
# Render build script
# https://render.com/docs/deploy-python

set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run database migrations/seeding
python -m data.seed

echo "Build completed successfully!"
