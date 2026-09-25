from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction

from judge.models import Language, Problem


class Command(BaseCommand):
    help = 'Register Elixir/Erlang and allow them on existing problems.'

    @transaction.atomic
    def handle(self, *args, **options):
        for key, name, mode, extension, template, description in [
            ('ELIXIR', 'Elixir', 'elixir', 'exs', 'IO.puts("Hello, world!")\n',
             'Elixir script (.exs), executed with one BEAM scheduler.'),
            ('ERLANG', 'Erlang', 'erlang', 'erl', 'main(_) ->\n    io:format("Hello, world!~n").\n',
             'Erlang escript (.erl). Entry point: main/1. No module declaration is required.'),
        ]:
            language, _ = Language.objects.update_or_create(key=key, defaults={
                'name': name, 'short_name': name, 'common_name': name, 'ace': mode,
                'pygments': mode, 'extension': extension, 'template': template, 'description': description,
            })
            for problem in Problem.objects.all():
                problem.allowed_languages.add(language)
        cache.clear()
        self.stdout.write('ELIXIR and ERLANG registered and enabled on existing problems.')
