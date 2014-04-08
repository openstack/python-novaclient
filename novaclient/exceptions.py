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

import inspect
import sys

import six

from novaclient.openstack.common.apiclient.exceptions import *  # noqa

# NOTE(akurilin): Since v.2.17.0 this alias should be left here to support
# backwards compatibility.
OverLimit = RequestEntityTooLarge


def _deprecate_code_attribute(slf):
    import warnings
    warnings.warn("'code' attribute is deprecated since v.2.17.0. Use "
                  "'http_status' instead of this one.", UserWarning)
    return slf.http_status

HttpError.code = property(_deprecate_code_attribute)


class NoTokenLookupException(ClientException):
    """This form of authentication does not support looking up
       endpoints from an existing token.
    """
    pass


class InstanceInErrorState(Exception):
    """Instance is in the error state."""
    pass


class RateLimit(RequestEntityTooLarge):
    """
    HTTP 429 - Rate limit: you've sent too many requests for this time period.
    """
    http_status = 429
    message = "Rate limit"


_code_map = dict(
    (getattr(obj, 'http_status', None), obj)
    for name, obj in six.iteritems(vars(sys.modules[__name__]))
    if inspect.isclass(obj) and getattr(obj, 'http_status', False)
)


class InvalidUsage(RuntimeError):
    """This function call is invalid in the way you are using this client.

    Due to the transition to using keystoneclient some function calls are no
    longer available. You should make a similar call to the session object
    instead.
    """
    pass


def from_response(response, body, url, method=None):
    """
    Return an instance of an HttpError or subclass
    based on an requests response.

    Usage::

        resp, body = requests.request(...)
        if resp.status_code != 200:
            raise exception_from_response(resp, rest.text)
    """
    kwargs = {
        'http_status': response.status_code,
        'method': method,
        'url': url,
        'request_id': None,
    }

    if response.headers:
        kwargs['request_id'] = response.headers.get('x-compute-request-id')

        if 'retry-after' in response.headers:
            kwargs['retry_after'] = response.headers.get('retry-after')

    if body:
        message = "n/a"
        details = "n/a"

        if hasattr(body, 'keys'):
            error = body[list(body)[0]]
            message = error.get('message')
            details = error.get('details')

        kwargs['message'] = message
        kwargs['details'] = details

    cls = _code_map.get(response.status_code, HttpError)

    return cls(**kwargs)
