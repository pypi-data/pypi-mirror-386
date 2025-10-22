from cassandra import InvalidRequest
from django.conf import settings
from django.core.management import BaseCommand
from django.db import connections, ConnectionProxy
from django.utils.timezone import now
from glob import glob
from importlib import import_module
from os.path import dirname, abspath, join, basename
from pathlib import Path
from dm_core.migrationcd.models import DjangoMigrationsCd
import logging
import sys
import time

logger = logging.getLogger()


class Command(BaseCommand):

    help = 'Migrate Cassandra DataModel'

    def add_arguments(self, parser):
        parser.add_argument("-d", "--direction", dest="action", nargs='?', help="up (default)/down")
        parser.add_argument("-a", "--app", required="--app" in sys.argv, type=str)

    def handle(self, *args, **kwargs):
        self._init_migration_cd()
        direction = kwargs.pop('direction', 'up')
        if direction == 'down':
            app = kwargs.pop('app')
            self.traverse_down(app)
        else:
            self.traverse_up()

    def _init_migration_cd(self):
        """
        Create the required meta table in cassandra
        """
        query = """
            create table if not exists django_migrations_cd
            (
            id text,
            app text,
            created_at timestamp,
            primary key (app, id)
            )
            with clustering order by (id DESC)
        """
        connection = ConnectionProxy(connections, 'cassandra')
        cursor = connection.cursor()
        cursor.execute(query)

    def traverse_down(self, app: str):
        migration = DjangoMigrationsCd.objects.filter(app=app).order_by('-id').first()
        migration_cls = getattr(import_module('.'.join([app, 'migrations_cd', migration.id])), 'MigrationCD')
        self._execute(migration_cls, 'down')
        migration.delete()

    def traverse_up(self):
        for app in settings.DM_LIBS + settings.DM_CUSTOM_APPS:
            app_module = import_module(app)
            if app_module.__file__ is None:
                logger.info("Skipping {}, as app_module.__file__ is None".format(app))
                continue
            app_dir = abspath(dirname(app_module.__file__))
            if Path(join(app_dir, 'migrations_cd')).is_dir():
                migration_cd = join(app_dir, 'migrations_cd', 'migration_[0-9][0-9][0-9]*')
                sorted_migrations = sorted(glob(migration_cd))
                for migration in sorted_migrations:
                    migration_id = basename(migration).split('.')[0]
                    migration_cls = self._get_migration_cls(app, migration_id)
                    if not self._is_migration_executed(migration_id):
                        self._execute(migration_cls)
                        self._log_executed(app, migration_id)
                else:
                    logger.info('All Cassandra migrations are up to date')

    def _get_migration_cls(self, app_module, migration: str):
        """
        Return the migration class
        """
        return getattr(import_module('.'.join([app_module, 'migrations_cd', migration])), 'MigrationCD')

    def _execute(self, migration_cls, direction='up'):
        """
        Execute the migration
        direction: up or down
        """
        if direction == 'down':
            migration_cls().down()
        else:
            migration_cls().up()

    def _log_executed(self, app: str, migration_id: str) -> None:
        """
        Record the migration that has been executed
        """
        retry = True
        while retry is True:
            try:
                DjangoMigrationsCd(id=migration_id, app=app, created_at=now()).save()
            except InvalidRequest as invalid_request:
                retry = True
                time.sleep(2)
            else:
                retry = False
        logger.info('Applied: {} {}'.format(app, migration_id))

    def _is_migration_executed(self, migration_id: str) -> bool:
        """
        Check if the migration has been executed
        """
        try:
            retry = True
            while retry is True:
                try:
                    DjangoMigrationsCd.objects.get(id=migration_id)
                except InvalidRequest as invalid_request:
                    retry = True
                    time.sleep(2)
                else:
                    retry = False
            return True
        except DjangoMigrationsCd.DoesNotExist:
            return False
