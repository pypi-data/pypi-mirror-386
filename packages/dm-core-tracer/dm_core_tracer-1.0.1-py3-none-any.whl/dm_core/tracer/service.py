from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from dm_core.crypto.asymmetric import AsymmetricCrypto
from dm_core.tracer.decorator import trace_http_consumer
from dm_core.tracer.exception import RequestsException
from requests.adapters import HTTPAdapter, Retry
from urllib.parse import urlparse
from .models import HttpLogModel
import time
import os
import enum
import logging
import requests
import json

logger = logging.getLogger()


class RequestAuthEnum(enum.Enum):
    INTERNAL = 'INTERNAL'
    EXTERNAL = 'EXTERNAL'
    ANONYMOUS = 'ANONYMOUS'


class Requests(object):
    """
    Requests wrapper class responsible for any internal communication

    All the internal API calls should adhere to following:
    - Add Trace ID to trace the HTTP call workflow via jaeger
    - Integrity on API calls i.e. APIs cannot be modified by anyone else
    - Stop replay attacks by limiting API to 60 seconds
    """

    def __init__(self, service: str, api_id: str, private_key=None):
        self.service = service
        self.api_id = api_id
        self.private_key = private_key
        self.timeout = int(os.getenv('ENV_SERVICES_TIMEOUT', '120'))
        self.max_retries = 5
        self.backoff_factor = 0.2
        self.retries = Retry(total=self.max_retries,
                             backoff_factor=self.backoff_factor,
                             status_forcelist=[500, 502, 503, 504])

    def __call__(self, method: str, url: str, request_auth=RequestAuthEnum.ANONYMOUS, *args, **kwargs):
        allowed_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD']
        if method not in allowed_methods:
            raise ValueError(f"{method} should be one of {allowed_methods}")
        if 'timeout' in kwargs:
            self.timeout = kwargs.pop('timeout')
        auth = kwargs.pop('auth', None)
        allow_redirects = kwargs.pop('allow_redirects', True)
        # Override json param from **kwargs
        json = kwargs.pop('jsonify', None)
        if json is not None:
            kwargs['json'] = self._json_ready(json)
        pre_request = requests.Request(method, url, *args, **kwargs)
        return self.trace_consumer(self.service, self.api_id, pre_request, request_auth, auth, allow_redirects, *args,
                                   **kwargs)

    def _json_ready(self, obj):
        # Convert datetimes, dates, Decimals, UUIDs, etc. to JSON-safe primitives
        # (strings/ints/floats/lists/dicts). Works recursively.
        return json.loads(json.dumps(obj, cls=DjangoJSONEncoder))

    @trace_http_consumer()
    def trace_consumer(self, span, pre_request, request_auth, auth, allow_redirects, *args, **kwargs):
        prepared_request = pre_request.prepare()

        if request_auth == RequestAuthEnum.INTERNAL:
            # Inject internal security headers
            prepared_request = self._inject_internal_auth_headers(prepared_request)
        elif request_auth == RequestAuthEnum.EXTERNAL and auth is not None:
            prepared_request = self._inject_external_auth_headers(prepared_request, auth)

        return self.send(span, prepared_request, allow_redirects)

    def _sign_hash(self, data: bytes):
        return AsymmetricCrypto(private_key=self.private_key).sign(data).hex()

    def _inject_internal_auth_headers(self, prepared_request: requests.PreparedRequest) -> requests.PreparedRequest:
        """
        Add internal security headers

        DM-SOURCE-SERVICE
        DM-ENCRYPTED-HASH
        DM-TIMESTAMP

        Only if private_key is given, service is not meta AND url has 'internal'
        """
        if self.private_key is None:
            return prepared_request
        if self.service == 'meta':
            return prepared_request
        if 'internal' not in prepared_request.url.split('/'):
            return prepared_request

        hashable_text = prepared_request.path_url
        prepared_request.headers['DM-TIMESTAMP'] = str(int(time.time()))
        prepared_request.headers['DM-SOURCE-SERVICE'] = settings.SERVICE
        hashable_text += prepared_request.headers['DM-TIMESTAMP']
        if prepared_request.body is not None:
            if isinstance(prepared_request.body, bytes):
                try:
                    hashable_text += prepared_request.body.decode()
                except UnicodeDecodeError as e:
                    pass
            else:
                hashable_text += prepared_request.body
        prepared_request.headers['DM-ENCRYPTED-HASH'] = self._sign_hash(hashable_text.encode())
        return prepared_request

    def _inject_external_auth_headers(self, prepared_request: requests.PreparedRequest,
                                      auth: str) -> requests.PreparedRequest:
        """
        Add external security headers

        AUTHORIZATION
        """
        prepared_request.headers['Authorization'] = f"Bearer {auth}"
        return prepared_request

    def _send(self, span, prepared_request, allow_redirects, *args, **kwargs):
        if prepared_request.body is not None and isinstance(prepared_request.body, bytes):
            try:
                body = prepared_request.body.decode()
            except UnicodeDecodeError as e:
                body = ''
        else:
            body = ''
        HttpLogModel.log_request(span.context.span_id,
                                 span.context.trace_id,
                                 dict(prepared_request.headers),
                                 prepared_request.url,
                                 body)
        try:
            protocol = urlparse(prepared_request.url).scheme
            self._request = prepared_request
            # Connection reset by peer, retry
            for attempt in range(self.max_retries):
                try:
                    session = requests.Session()
                    session.mount(protocol, HTTPAdapter(max_retries=self.retries))
                    response = session.send(prepared_request, timeout=self.timeout, allow_redirects=allow_redirects)
                    break
                except requests.exceptions.ConnectionError as connection_error:
                    if attempt < self.max_retries - 1:
                        backoff_time = self.backoff_factor * (2 ** attempt)
                        logging.info(f"Retrying {prepared_request.url} in {backoff_time} seconds...")
                        time.sleep(backoff_time)
                    else:
                        raise connection_error
        except requests.exceptions.Timeout as timeout_exception:
            raise RequestsException(timeout_exception, span.context.span_id)
        except requests.exceptions.TooManyRedirects as too_many_redirects:
            raise RequestsException(too_many_redirects, span.context.span_id)
        except requests.exceptions.ConnectionError as connection_error:
            raise RequestsException(connection_error, span.context.span_id)
        except requests.exceptions.RequestException as request_exception:
            raise RequestsException(request_exception, span.context.span_id)
        else:
            HttpLogModel.log_response(span.context.span_id,
                                      span.context.trace_id,
                                      dict(prepared_request.headers),
                                      response.url,
                                      response.content.decode())
        return response, prepared_request

    def send(self, span, prepared_request, allow_redirects):
        return self._send(span, prepared_request, allow_redirects)
