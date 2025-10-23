from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.urls import resolve
from dm_core.tracer.constants import TraceTag, SpanKind
from opentelemetry.propagate import inject, extract
import logging

logger = logging.getLogger()


@staticmethod
def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    elif request.META.get('HTTP_X_REAL_IP'):
        ip = request.META.get('HTTP_X_REAL_IP')
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def trace_http_consumer():
    """
    Decorator for http consumer

    In other words, the service implementing HTTP Client to talk to other services invokes http_consumer to inject Jaeger tracer information

    @param: target_service: Name of the service being invoked
    @param: api_id: rest_api ID defined in meta service
    @param: pre_request: Request to be sent
    """
    def wrapper(func):
        def f(obj, target_service, api_id, pre_request, *args, **kwargs):
            _tracer = settings.TRACER
            with _tracer.start_as_current_span(name='{}.{}'.format(target_service, api_id)) as span:
                span.set_attribute(TraceTag.HTTP_METHOD.value, pre_request.method)
                span.set_attribute(TraceTag.HTTP_URL.value, pre_request.url)
                span.set_attribute(TraceTag.SERVICE.value, settings.SERVICE)
                span.set_attribute(TraceTag.SPAN_KIND.value, SpanKind.HTTP_CLIENT.value)
                span.set_attribute(TraceTag.PEER_SERVICE.value, target_service)
                inject(pre_request.headers)
                logger.debug('http_consumer: {} {}.{}'.format(settings.SERVICE, target_service, api_id))
                return func(obj, span, pre_request, *args, **kwargs)
        return f
    return wrapper


def trace_http_provider():
    """
    Decorator for http provider

    - Employed in Django middleware
    - Wrapped with decorator trace_http
    """
    def wrapper(func):
        def f(obj, request: WSGIRequest):
            _tracer = settings.TRACER
            _span_ctx = extract(request.headers)
            view = resolve(request.path).func
            request.span = None
            if not hasattr(view, 'cls') or not hasattr(view.cls, 'api_id') or request.method not in view.cls.api_id:
                return func(obj, request)
            api_id = view.cls.api_id
            with _tracer.start_as_current_span(name='{}'.format(api_id[request.method]),
                                               context=_span_ctx) as span:
                span.set_attribute(TraceTag.HTTP_METHOD.value, request.method)
                span.set_attribute(TraceTag.HTTP_URL.value, request.build_absolute_uri())
                span.set_attribute(TraceTag.SERVICE.value, settings.SERVICE)
                span.set_attribute(TraceTag.PEER_HOST_IPV4.value, _get_client_ip(request))
                span.set_attribute(TraceTag.SPAN_KIND.value, SpanKind.HTTP_SERVER.value)
                request.span = span
                logger.debug('http_provider: {}: {}'.format(span.context.span_id, api_id))
                return func(obj, request)
        return f
    return wrapper


def trace_message_producer():
    """
    Decorate trace_message_producer: Used when producing for Rabbit MQ message sender

    Sets the required information for the Jaeger tracer : topic, message_id, request_id
    `topic` is appropriate name in the world of RabbitMq. It is also called `routing_key` in meta_service context

    This decorator is used in dm_core.rabbit, but the dm_core.rabbit library itself is used in every other service
    """
    def wrapper(func):
        def f(obj, exchange_key, routing_key, data, *args, **kwargs):
            _tracer = settings.TRACER
            carrier = {}
            with _tracer.start_as_current_span(name=f"MSGPRODUCER:{exchange_key}:{routing_key}") as span:
                span.set_attribute(TraceTag.SPAN_KIND.value, SpanKind.MESSAGE_PRODUCER.value)
                span.set_attribute(TraceTag.EXCHANGE_KEY.value, exchange_key)
                span.set_attribute(TraceTag.ROUTING_KEY.value, routing_key)
                span.set_attribute(TraceTag.MESSAGE_ID.value, data.message_id)
                span.set_attribute(TraceTag.REQUEST_ID.value, data.request_id)
                span.set_attribute(TraceTag.SERVICE.value, settings.SERVICE)
                inject(carrier)
                logger.debug('trace_message_producer: {} {} {}'.format(span, exchange_key, routing_key))
                return func(obj, exchange_key, routing_key, data, carrier, *args, **kwargs)
        return f
    return wrapper


def trace_message_consumer():
    """
    Decorate for Rabbit MQ message receiver

    This decorator is used in dm_core.rabbit, but the dm_core.rabbit library itself is used in every other service

    Trace Event Consumer: Decorater for the method that receives the messages from RabbitMQ

    `topic` is appropriate name in the world of RabbitMq. It is also called `routing_key` in meta_service context
    """
    def wrapper(func):
        def f(obj, method, message, properties, *args, **kwargs):
            _tracer = settings.TRACER
            _span_ctx = extract(properties.headers)
            with _tracer.start_as_current_span(name=f"MSGCONSUMER:{method.consumer_tag}", context=_span_ctx) as span:
                span.set_attribute(TraceTag.SPAN_KIND.value, SpanKind.MESSAGE_CONSUMER.value)
                span.set_attribute(TraceTag.SERVICE.value, settings.SERVICE)
                if hasattr(method, 'exchange_key'):
                    span.set_attribute(TraceTag.EXCHANGE_KEY.value, method.exchange_key)
                else:
                    span.set_attribute(TraceTag.EXCHANGE_KEY.value, method.exchange)
                span.set_attribute(TraceTag.QUEUE_ID.value, method.consumer_tag)
                span.set_attribute(TraceTag.ROUTING_KEY.value, method.routing_key)
                span.set_attribute(TraceTag.MESSAGE_ID.value, message.message_id)
                span.set_attribute(TraceTag.REQUEST_ID.value, message.request_id)
                logger.debug('trace_message_consumer: {} {} {}'.format(span, method.exchange, method.routing_key))
                return func(obj, method, message, properties, *args, **kwargs)
        return f
    return wrapper


def trace_event_producer():
    """
    Decorator for OBJECT METHODS who want to send jobs via redis queue
    """
    def wrapper(func):
        def f(obj, data, *args, **kwargs):
            _tracer = settings.TRACER
            carrier = {}
            fn_name = '{}.{}.{}.{}'.format(settings.SERVICE, obj.__class__.__module__, obj.__class__.__name__, func.__name__)
            with _tracer.start_as_current_span(name=f"EVNTPRODUCER:{fn_name}") as span:
                span.set_attribute(TraceTag.SPAN_KIND.value, SpanKind.PROCESS_PRODUCER.value)
                span.set_attribute(TraceTag.SERVICE.value, settings.SERVICE)
                span.set_attribute('func', fn_name)
                inject(carrier)
                logger.debug('trace_event_producer: {} {}'.format(span, fn_name))
                return func(obj, data, carrier, *args, **kwargs)
        return f
    return wrapper


def trace_event_consumer():
    """
    Decorator for METHODS to receive the jobs via redis queue
    """
    def wrapper(func):
        def f(data, properties: dict, *args, **kwargs):
            _tracer = settings.TRACER
            _span_ctx = extract(properties)
            fn_name = '{}.{}.{}'.format(settings.SERVICE, func.__module__, func.__name__)
            with _tracer.start_as_current_span(name=f"EVNTCONSUMER:{fn_name}", context=_span_ctx) as span:
                span.set_attribute(TraceTag.SPAN_KIND.value, SpanKind.PROCESS_CONSUMER.value)
                span.set_attribute(TraceTag.SERVICE.value, settings.SERVICE)
                span.set_attribute(TraceTag.FUNC.value, fn_name)
                logger.debug('trace_event_consumer: {} {}'.format(span, fn_name))
                return func(data, *args, **kwargs)
        return f
    return wrapper


def trace():
    """
    Decorator for METHODS to track the calls between methods
    """
    def wrapper(func):
        def f(obj, *args, **kwargs):
            _tracer = settings.TRACER
            method = '{}:{}'.format(obj.__class__.__name__, func.__name__)
            with _tracer.start_as_current_span(method) as span:
                return func(obj, *args, **kwargs)
        return f
    return wrapper


def trace_method():
    """
    Decorator for FUNCTIONS to track the calls between methods
    """
    def wrapper(func):
        def f(*args, **kwargs):
            _tracer = settings.TRACER
            method = '{}'.format(func.__name__)
            with _tracer.start_as_current_span(method) as span:
                return func(*args, **kwargs)
        return f
    return wrapper
