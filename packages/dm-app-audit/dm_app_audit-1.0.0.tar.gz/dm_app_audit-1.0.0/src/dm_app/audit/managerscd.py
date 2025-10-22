from django_cassandra_engine.models import DjangoCassandraQuerySet


class EventLogCdManager(DjangoCassandraQuerySet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
