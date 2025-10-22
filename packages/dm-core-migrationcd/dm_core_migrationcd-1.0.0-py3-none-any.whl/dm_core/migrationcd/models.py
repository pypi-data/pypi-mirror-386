from django.utils.timezone import now
from django_cassandra_engine.models import DjangoCassandraModel
from cassandra.cqlengine import columns
from .abc import DmDjangoCassandraModelABC


class DjangoMigrationsCd(DmDjangoCassandraModelABC, DjangoCassandraModel):
    app = columns.Text(primary_key=True, partition_key=True)
    id = columns.Text(primary_key=True, clustering_order='DESC')
    created_at = columns.DateTime(default=now)

    class Meta:
        managed = False
        db_table = 'django_migrations_cd'
        get_pk_field = 'id'

    @classmethod
    def db_name(cls):
        return 'django_migrations_cd'