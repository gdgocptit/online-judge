"""Run with manage.py shell to register the local BEAM judge and languages."""
import os
import secrets
from pathlib import Path

import yaml
from django.conf import settings
from django.core.management import call_command

from judge.models import Judge

if not settings.DEBUG or settings.DATABASES['default']['HOST'] not in ('localhost', '127.0.0.1'):
    raise RuntimeError('This setup is only for the local development database.')

call_command('register_beam_languages')
judge, _ = Judge.objects.get_or_create(name='local-beam', defaults={
    'auth_key': secrets.token_urlsafe(32), 'description': 'Local Elixir and Erlang judge',
})

config_path = Path(os.environ.get('DMOJ_BEAM_CONFIG', '../.local/beam-judge.yml')).resolve()
config_path.parent.mkdir(parents=True, exist_ok=True)
with config_path.open('w') as config:
    yaml.safe_dump({
        'id': judge.name, 'key': judge.auth_key, 'problem_storage_globs': ['/problems/*'],
        'runtime': {'elixir': '/opt/elixir/bin/elixir', 'escript': '/usr/local/bin/escript',
                    'erl': '/usr/local/bin/erl'},
    }, config)
print(f'Registered ELIXIR, ERLANG and {judge.name}; configuration: {config_path}')
