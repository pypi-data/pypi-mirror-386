from abc import ABC
from django.db import connections
from django.utils.connection import ConnectionProxy


class AbstractMigrationCD(ABC):

    def __init__(self):
        self._connection = ConnectionProxy(connections, 'cassandra')
        self._keyspace = self._connection.settings_dict['NAME']


class DmDjangoCassandraModelABC():
    """
    DmDjangoCassandraModel: Use it with every DjangoCassandraModel class inheritance

    Avoiding to repeat the below classmethod, they have been defined in DmDjangoCassandraModelABC

    Note: DmDjangoCassandraModelABC cannot be inherited by ABC, since the DjangoCassandraModel metaclass definition
    prevents us from doing so
    """

    @classmethod
    def _raw_column_family_name(cls, *args, **kwargs):
        name = super(DmDjangoCassandraModelABC, cls)._raw_column_family_name(*args, **kwargs)
        namespace = f"{name.split('.')[0]}.{cls.db_name()}" if len(name.split('.')) > 1 else cls.db_name()
        return namespace

    @classmethod
    def column_family_name(cls, *args, **kwargs):
        name = super(DmDjangoCassandraModelABC, cls).column_family_name(*args, **kwargs)
        namespace = f"{name.split('.')[0]}.{cls.db_name()}" if len(name.split('.')) > 1 else cls.db_name()
        return namespace
