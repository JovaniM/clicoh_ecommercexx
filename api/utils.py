import requests
from requests.adapters import HTTPAdapter
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler
from urllib3.util.retry import Retry


class CustomValidationError(APIException):
    def __init__(self, error, status_code, error_detail=None, errors=[]):
        self.error = error
        self.status = status_code
        self.error_detail = error_detail
        self.detail = self.error_detail if self.error_detail else self.error
        self.errors = errors

    def __str__(self):
        return f"{self.error}"


def requests_retry_session(
    retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504), session=None
):
    session = session or requests.Session()

    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def custom_exception_handler(exc, context):
    handlers = {
        'CustomValidationError': _handle_custom_validation_error,
    }

    response = exception_handler(exc, context)
    exception_class = exc.__class__.__name__
    if exception_class in handlers:
        return handlers[exception_class](exc, context, response)
    return response


def _handle_custom_validation_error(exc, context, response):
    message = exc.error
    status = exc.status
    return http_error_response(message, status)

def http_error_response(message, status_code):
    return Response({"ok": False, "message": message}, status=status_code)


def http_success_response(data, status_code):
    return Response(data, status=status_code)
