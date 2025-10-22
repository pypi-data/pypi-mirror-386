from cassandra.cqlengine import columns
from django_cassandra_engine.models import DjangoCassandraModel
from datetime import datetime
from dm_core.migrationcd.abc import DmDjangoCassandraModelABC
from .managerscd import EventLogCdManager
import uuid


def uuid_generator():
    return uuid.uuid4().hex


class EventLogModelCd(DmDjangoCassandraModelABC, DjangoCassandraModel):
    id = columns.Text(primary_key=True, default=uuid_generator)
    created_at = columns.DateTime(index=True, default=datetime.utcnow)
    event_type = columns.Text(index=True, required=True)
    resource_id = columns.Text(index=True, required=True, max_length=32)
    application = columns.Text(required=True, max_length=128)
    data = columns.Blob()

    class Meta:
        get_pk_field = 'id'
        managed = False
        db_table = 'dm_app_audit_event_log'

    __queryset__ = EventLogCdManager

    @classmethod
    def db_name(cls):
        return 'dm_app_audit_event_log'
