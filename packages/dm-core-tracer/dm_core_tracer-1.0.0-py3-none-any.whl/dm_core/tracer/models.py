from cassandra.cqlengine import columns
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import JSONField
from django.utils import timezone
from django_cassandra_engine.models import DjangoCassandraModel
from dm_core.migrationcd.abc import DmDjangoCassandraModelABC


class MessageLogModel(models.Model):
    """
    Model to trace the messages received.
    This will help in eliminating the duplicate messages
    """
    message_id = models.CharField(max_length=255, db_index=True)
    request_id = models.CharField(max_length=255)
    timestamped = models.DateTimeField(default=timezone.now, editable=False)
    exchange_key = models.CharField(max_length=255, db_index=True)
    routing_key = models.CharField(max_length=255, db_index=True)
    direction = models.CharField(max_length=255)
    data = JSONField(encoder=DjangoJSONEncoder)

    class Meta:
        db_table = 'tracer_message_log'
        unique_together = (('message_id', 'direction'),)


class HttpLogModel(models.Model):
    """
    Model to trace incoming and outgoing Http REST requests/responses
    """
    trace_id = models.CharField(max_length=32, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    span_id = models.CharField(max_length=32, db_index=True)
    body = JSONField(encoder=DjangoJSONEncoder)
    headers = JSONField(encoder=DjangoJSONEncoder)
    url_path = models.CharField(max_length=8092)

    def __str__(self):
        return self._id

    @classmethod
    def log_request(cls,span_id: int, trace_id: int, headers: dict, url_path: str, body: str|bytes=''):
        if isinstance(body, bytes):
            try:
                body = body.decode()
            except UnicodeDecodeError:
                body = ''
        cls.objects.create(span_id='{:x}:req'.format(span_id), trace_id='{:x}'.format(trace_id), headers=headers, url_path=url_path, body=body)

    @classmethod
    def log_response(cls,span_id: int, trace_id: int, headers: dict, url_path: str, body: str|bytes=''):
        if isinstance(body, bytes):
            try:
                body = body.decode()
            except UnicodeDecodeError:
                body = ''
        cls.objects.create(span_id='{:x}:res'.format(span_id), trace_id='{:x}'.format(trace_id), headers=headers, url_path=url_path, body=body)


class MessageLogCdModel(DmDjangoCassandraModelABC, DjangoCassandraModel):
    """
    Model to trace the messages received.
    Archive logs from Postgresql that are older than X units
    """

    message_id = columns.Text(primary_key=True)
    request_id = columns.Text(required=True)
    timestamped = columns.DateTime(index=True)
    exchange_key = columns.Text(index=True)
    routing_key = columns.Text(index=True)
    direction = columns.Text(max_length=255)
    data = columns.Text()

    class Meta:
        get_pk_field = 'message_id'
        managed = False
        db_table = 'dm_core_tracer_message_log'

    @classmethod
    def db_name(cls):
        return 'dm_core_tracer_message_log'


class HttpLogCdModel(DmDjangoCassandraModelABC, DjangoCassandraModel):
    """
    Model to trace incoming and outgoing Http REST requests/responses
    Archive logs from Postgresql that are older than X units
    """
    span_id = columns.Text(primary_key=True)
    trace_id = columns.Text(max_length=32, index=True)
    created_at = columns.DateTime(index=True)
    body = columns.Text()
    headers = columns.Text()
    url_path = columns.Text(max_length=8092)

    class Meta:
        get_pk_field = 'span_id'
        managed = False
        db_table = 'dm_core_tracer_http_log'

    @classmethod
    def db_name(cls):
        return 'dm_core_tracer_http_log'
