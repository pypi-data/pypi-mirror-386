from .decorator import trace_http_provider
from .constants import TraceTag
from .models import HttpLogModel


class TracerMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response
        self.span = None

    def __call__(self, request):
        no_trace = request.headers.get('DM-TRACE', None)
        if no_trace is None:
            return self.process_request(request)
        else:
            return self.get_response(request)

    def _get_body(self, request):
        try:
            return request.body.decode()
        except:
            return ''

    @trace_http_provider()
    def process_request(self, request):
        if request.span is not None:
            HttpLogModel.log_request(span_id=request.span.context.span_id,
                                       trace_id=request.span.context.trace_id,
                                       url_path=request.path_info,
                                       body=self._get_body(request),
                                       headers=request.headers.__dict__)
            response = self.get_response(request)
            self.process_response(request, response)
            return response
        else:
            return self.get_response(request)

    def process_response(self, request, response):
        span = request.span
        response['Trace-Id'] = '{:x}:{:016x}'.format(span.context.trace_id, span.context.span_id)
        HttpLogModel.log_response(span_id=span.context.span_id,
                             trace_id=span.context.trace_id,
                             url_path=request.path_info,
                             body=self._get_body(request),
                             headers=response.headers.__dict__)
        response['DM-LOG-ID'] = '{:x}'.format(span.context.trace_id)
        return response

    def process_exception(self, request, exception):
        if hasattr(request, 'span') and request.span is not None:
            request.span.set_attribute(TraceTag.ERROR.value, True)
            request.span.record_exception(exception)
        return None