#!/bin/bash
# Run as root on the existing VPS. Configuration and data stay outside Git.
set -euo pipefail
cd /srv/dmoj/site
if [[ -n $(git status --porcelain) ]]; then
    echo 'Working tree has local changes; commit or save them before deploying.' >&2
    exit 1
fi
bash /srv/dmoj/backup.sh
git pull --ff-only origin master
git submodule update --init --recursive
export PATH=/srv/dmoj/venv/bin:$PATH
uv pip install --python /srv/dmoj/venv/bin/python -r requirements.txt mysqlclient uwsgi 'redis<6' websocket-client setuptools
npm ci --no-audit --no-fund
python manage.py check
./make_style.sh
python manage.py compilemessages
python manage.py compilejsi18n
python manage.py collectstatic --noinput
python manage.py migrate --noinput
chown -R dmoj:dmoj /srv/dmoj/static
systemctl restart dmoj-web dmoj-bridge dmoj-celery dmoj-events
systemctl is-active dmoj-web dmoj-bridge dmoj-celery dmoj-events
curl --fail --silent --show-error --retry 10 --retry-connrefused --retry-delay 2 \
    -H 'Host: fpt.nguyenchinh.dev' -H 'X-Forwarded-Proto: https' \
    http://127.0.0.1:8000/ -o /dev/null
echo "Website deployed: $(git rev-parse HEAD)"
