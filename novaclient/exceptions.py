# Copyright 2010 Jacob Kaplan-Moss
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Exception definitions.
"""


class UnsupportedVersion(Exception):
    """Indicates that the user is trying to use an unsupported
    version of the API.
    """
    pass


class UnsupportedConsoleType(Exception):
    """Indicates that the user is trying to use an unsupported
    console type when retrieving console urls of servers.
    """
    def __init__(self, console_type):
        self.message = 'Unsupported console_type "%s"' % console_type


class UnsupportedAttribute(AttributeError):
    """Indicates that the user is trying to transmit the argument to a method,
    which is not supported by selected version.
    """

    def __init__(self, argument_name, start_version, end_version=None):
        if end_version:
            self.message = (
                "'%(name)s' argument is only allowed for microversions "
                "%(start)s - %(end)s." % {"name": argument_name,
                                          "start": start_version,
                                          "end": end_version})
        else:
            self.message = (
                "'%(name)s' argument is only allowed since microversion "
                "%(start)s." % {"name": argument_name, "start": start_version})
        super(UnsupportedAttribute, self).__init__(self.message)


class CommandError(Exception):
    pass


class AuthorizationFailure(Exception):
    pass


class NoUniqueMatch(Exception):
    pass


class NoTokenLookupException(Exception):
    """This form of authentication does not support looking up
       endpoints from an existing token.
    """
    pass


class EndpointNotFound(Exception):
    """Could not find Service or Region in Service Catalog."""
    pass


class AmbiguousEndpoints(Exception):
    """Found more than one matching endpoint in Service Catalog."""
    def __init__(self, endpoints=None):
        self.endpoints = endpoints

    def __str__(self):
        return "AmbiguousEndpoints: %s" % repr(self.endpoints)


class ConnectionRefused(Exception):
    """
    Connection refused: the server refused the connection.
    """
    def __init__(self, response=None):
        self.response = response

    def __str__(self):
        return "ConnectionRefused: %s" % repr(self.response)


class ResourceInErrorState(Exception):
    """Resource is in the error state."""

    def __init__(self, obj):
        msg = "`%s` resource is in the error state" % obj.__class__.__name__
        fault_msg = getattr(obj, "fault", {}).get("message")
        if fault_msg:
            msg += "due to '%s'" % fault_msg
        self.message = "%s." % msg


class VersionNotFoundForAPIMethod(Exception):
    msg_fmt = "API version '%(vers)s' is not supported on '%(method)s' method."

    def __init__(self, version, method):
        self.version = version
        self.method = method

    def __str__(self):
        return self.msg_fmt % {"vers": self.version, "method": self.method}


class InstanceInDeletedState(Exception):
    """Instance is in the deleted state."""
    pass


class ClientException(Exception):
    """
    The base exception class for all exceptions this library raises.
    """
    message = 'Unknown Error'

    def __init__(self, code, message=None, details=None, request_id=None,
                 url=None, method=None):
        self.code = code
        self.message = message or self.__class__.message
        self.details = details
        self.request_id = request_id
        self.url = url
        self.method = method

    def __str__(self):
        formatted_string = "%s (HTTP %s)" % (self.message, self.code)
        if self.request_id:
            formatted_string += " (Request-ID: %s)" % self.request_id

        return formatted_string


class RetryAfterException(ClientException):
    """
    The base exception class for ClientExceptions that use Retry-After header.
    """
    def __init__(self, *args, **kwargs):
        try:
            self.retry_after = int(kwargs.pop('retry_after'))
        except (KeyError, ValueError):
            self.retry_after = 0

        super(RetryAfterException, self).__init__(*args, **kwargs)


class BadRequest(ClientException):
    """
    HTTP 400 - Bad request: you sent some malformed data.
    """
    http_status = 400
    message = "Bad request"


class Unauthorized(ClientException):
    """
    HTTP 401 - Unauthorized: bad credentials.
    """
    http_status = 401
    message = "Unauthorized"


class Forbidden(ClientException):
    """
    HTTP 403 - Forbidden: your credentials don't give you access to this
    resource.
    """
    http_status = 403
    message = "Forbidden"


class NotFound(ClientException):
    """
    HTTP 404 - Not found
    """
    http_status = 404
    message = "Not found"


class MethodNotAllowed(ClientException):
    """
    HTTP 405 - Method Not Allowed
    """
    http_status = 405
    message = "Method Not Allowed"


class NotAcceptable(ClientException):
    """
    HTTP 406 - Not Acceptable
    """
    http_status = 406
    message = "Not Acceptable"


class Conflict(ClientException):
    """
    HTTP 409 - Conflict
    """
    http_status = 409
    message = "Conflict"


class OverLimit(RetryAfterException):
    """
    HTTP 413 - Over limit: you're over the API limits for this time period.
    """
    http_status = 413
    message = "Over limit"


class RateLimit(RetryAfterException):
    """
    HTTP 429 - Rate limit: you've sent too many requests for this time period.
    """
    http_status = 429
    message = "Rate limit"


# NotImplemented is a python keyword.
class HTTPNotImplemented(ClientException):
    """
    HTTP 501 - Not Implemented: the server does not support this operation.
    """
    http_status = 501
    message = "Not Implemented"


# In Python 2.4 Exception is old-style and thus doesn't have a __subclasses__()
# so we can do this:
#     _code_map = dict((c.http_status, c)
#                      for c in ClientException.__subclasses__())
#
# Instead, we have to hardcode it:
_error_classes = [BadRequest, Unauthorized, Forbidden, NotFound,
                  MethodNotAllowed, NotAcceptable, Conflict, OverLimit,
                  RateLimit, HTTPNotImplemented]
_code_map = dict((c.http_status, c) for c in _error_classes)


class InvalidUsage(RuntimeError):
    """This function call is invalid in the way you are using this client.

    Due to the transition to using keystoneauth some function calls are no
    longer available. You should make a similar call to the session object
    instead.
    """
    pass


def from_response(response, body, url, method=None):
    """
    Return an instance of an ClientException or subclass
    based on a requests response.

    Usage::

        resp, body = requests.request(...)
        if resp.status_code != 200:
            raise exception_from_response(resp, rest.text)
    """
    cls = _code_map.get(response.status_code, ClientException)

    kwargs = {
        'code': response.status_code,
        'method': method,
        'url': url,
        'request_id': None,
    }

    if response.headers:
        kwargs['request_id'] = response.headers.get('x-compute-request-id')

        if (issubclass(cls, RetryAfterException) and
                'retry-after' in response.headers):
            kwargs['retry_after'] = response.headers.get('retry-after')

    if body:
        message = "n/a"
        details = "n/a"

        if hasattr(body, 'keys'):
            # NOTE(mriedem): WebOb<1.6.0 will return a nested dict structure
            # where the error keys to the message/details/code. WebOb>=1.6.0
            # returns just a response body as a single dict, not nested,
            # so we have to handle both cases (since we can't trust what we're
            # given with content_type: application/json either way.
            if 'message' in body:
                # WebOb 1.6.0 case
                message = body.get('message')
                details = body.get('details')
            else:
                # WebOb<1.6.0 where we assume there is a single error message
                # key to the body that has the message and details.
                error = body[list(body)[0]]
                message = error.get('message')
                details = error.get('details')

        kwargs['message'] = message
        kwargs['details'] = details

    return cls(**kwargs)


class ResourceNotFound(Exception):
    """Error in getting the resource."""
    pass
