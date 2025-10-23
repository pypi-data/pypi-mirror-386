from enum import Enum


class TraceTag(Enum):
    EXCHANGE_KEY = "exchange.key"
    ERROR = "error"
    FUNC = "func"
    HTTP_METHOD = "http.method"
    HTTP_URL = "http.url"
    MESSAGE_ID = "message.id"
    PEER_HOST_IPV4 = 'peer.ipv4'
    PEER_SERVICE = "peer.service"
    REQUEST_ID = "request.id"
    ROUTING_KEY = "routing.key"
    SPAN_KIND = "span.kind"
    SERVICE = "service"
    QUEUE_ID = "queue.id"

    def __str__(self):
        return '%s' % self.value


class SpanKind(Enum):
    INTERNAL = "internal"
    HTTP_CLIENT = "http.client"
    HTTP_SERVER = "http.server"
    PROCESS_CONSUMER = "process.consumer"
    PROCESS_PRODUCER = "process.producer"
    MESSAGE_CONSUMER = "message.consumer"
    MESSAGE_PRODUCER = "message.producer"


    def __str__(self):
        return '%s' % self.value
