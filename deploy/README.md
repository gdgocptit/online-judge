# VPS updates

Push changes to `gdgocptit/online-judge`, branch `master`, then SSH to the VPS:

```sh
bash /srv/dmoj/site/deploy/update.sh
```

This backs up the database/configuration/data, pulls with `--ff-only`, installs
dependencies, builds CSS/translations/static files, applies migrations and restarts
the web, bridge, Celery and event services. A local HTTP check must pass.
Use a quiet period: restarts briefly interrupt requests and judge connections.

Production settings (`dmoj/local_settings.py`, `websocket/config.js`) remain
ignored by Git. Never replace them with the local development examples.
Do not rerun the original `configure.py` or `seed.py` during normal updates.
Review dependency and database migration changes before deploying. Database
migrations can require restoring a backup for rollback.

Judge code has a separate update command:

```sh
bash /srv/dmoj/judge-server/deploy/update.sh
```

See that repository's `deploy/README.md`. Judge updates rebuild a Docker image;
pulling the source alone does not update a running worker.
