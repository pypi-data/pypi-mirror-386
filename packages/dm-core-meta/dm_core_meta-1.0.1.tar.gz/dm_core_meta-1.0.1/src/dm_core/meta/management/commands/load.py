from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import IntegrityError
from dm_core.crypto.symmetric import SymmetricCrypto
from dm_core.meta.models import AppConfigModel
from io import StringIO
from os import getenv
from os import path
from string import Template
import os
import sys
import json


class CustomTemplate(Template):
    delimiter = '$$'


class Command(BaseCommand):
    help = 'Load initial DM data fixtures - Postgres and Cassandra'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.env = getenv('ENV_SERVICES_ENV')
        service = settings.SERVICE
        fernet_key = getattr(settings, f"{service.upper()}_FERNET_KEY")
        self.crypto = SymmetricCrypto(fernet_key)
        self.kwargs = {}

    @property
    def apps(self):
        from django.apps import apps
        return list(apps.get_app_configs())

    def _get_file(self, app):
        return app.module.__file__

    def _load_unencrypted_fixtures(self):
        file = 'initial_postgres_data'
        load = False
        for app in list(self.apps):
            app_dir = path.dirname(app.module.__file__)
            app_fixture = path.join(app_dir, 'fixtures', f"{file}.json")
            if path.exists(app_fixture):
                with open(app_fixture, 'r') as app_ptr:
                    fixtures_data = app_ptr.readlines()
                json_fixtures = json.loads(''.join(fixtures_data))
                if type(json_fixtures) is list and len(json_fixtures) > 0:
                    load = True
        if load:
            call_command('loaddata', 'initial_postgres_data', **self.kwargs)

    def _load_encrypted_postgres(self):
        """
        Get list of installed apps and look for fixtures - initial_postgres_data_encrypted_{env}.json
        """
        for app in self.apps:
            try:
                app_dir = path.dirname(self._get_file(app))
                app_fixture = path.join(app_dir, 'fixtures', 'initial_postgres_data_encrypted_{}.json'.format(self.env))
                if path.exists(app_fixture):
                    decrypted_data = self._unencrypt(app_fixture)
                    if len(decrypted_data) == 0:
                        sys.stdout.write('Empty file found, skipping of encryption load')
                        return
                    decrypted_data_env = CustomTemplate(decrypted_data).substitute(**os.environ)
                    sys.stdin = StringIO(decrypted_data_env)
                    call_command('loaddata', '--format', 'json', '-', **self.kwargs)
            except IntegrityError as e:
                sys.stdout.write(f"Key already exists, skipping for {app}")
                sys.stdout.write(e)
            except ImportError as e:
                sys.stderr.write('Unable to import app ')
                sys.stderr.write(e)

    def _unencrypt(self, app_fixture):
        """
        Unencrypt the existing file
        """
        unencrypted_data = self.crypto.decrypt_file_to_data(app_fixture)
        return unencrypted_data.decode()

    def _fixtures_disabled(self):
        try:
            return AppConfigModel.objects.get(key='FIXTURES').value.get('disabled', False)
        except AppConfigModel.DoesNotExist as d:
            return False

    def handle(self, *args, **kwargs):
        self.kwargs = kwargs
        if self._fixtures_disabled():
            sys.stderr.write('Fixtures loading disabled\n')
        else:
            # Load postgresql
            self._load_unencrypted_fixtures()
            # Load encrypted postgresql
            self._load_encrypted_postgres()

