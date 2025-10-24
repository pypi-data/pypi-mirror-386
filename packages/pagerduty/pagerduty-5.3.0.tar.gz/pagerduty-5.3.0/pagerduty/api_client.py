# Core
import logging
import sys
import time

from copy import deepcopy
from random import random
from typing import Optional, Union
from warnings import warn

# PyPI
from requests import Response, Session
from requests import __version__ as REQUESTS_VERSION
from requests.exceptions import RequestException
from urllib3.exceptions import PoolError
from urllib3.exceptions import HTTPError as Urllib3HttpError

# Local
from . auth_method import AuthMethod
from . version import __version__
from . errors import (
    Error,
    HttpError
)
from . common import (
    TIMEOUT,
    normalize_url
)

class ApiClient(Session):
    """
    Base class for making HTTP requests to PagerDuty APIs

    This is an opinionated wrapper of `requests.Session`_, with a few additional
    features:

    - The client will reattempt the request with auto-increasing cooldown/retry
      intervals, with attempt limits configurable through the :attr:`retry`
      attribute.
    - When making requests, headers specified ad-hoc in calls to HTTP verb
      functions will not replace, but will be merged into, default headers.
    - The request URL, if it doesn't already start with the REST API base URL,
      will be prepended with the default REST API base URL.
    - It will only perform requests with methods as given in the
      :attr:`permitted_methods` list, and will raise :class:`Error` for
      any other HTTP methods.

    :param auth_method:
        The authentication method to use for API requests, should be an instance
        of the AuthMethod class.
    :param debug:
        Sets :attr:`print_debug`. Set to ``True`` to enable verbose command line
        output.
    """

    log = None
    """
    A ``logging.Logger`` object for logging messages. By default it is
    configured without any handlers and so no messages will be emitted. See:
    `Logger Objects
    <https://docs.python.org/3/library/logging.html#logger-objects>`_.
    """

    max_http_attempts = 10
    """
    The number of times that the client will retry after error statuses, for any
    that are defined greater than zero in :attr:`retry`.
    """

    max_network_attempts = 3
    """
    The number of times that connecting to the API will be attempted before
    treating the failure as non-transient; a :class:`Error` exception
    will be raised if this happens.
    """

    parent = None
    """The ``super`` object (`requests.Session`_)"""

    permitted_methods = ()
    """
    A tuple of the methods permitted by the API which the client implements.

    For instance:

    * The REST API accepts GET, POST, PUT and DELETE.
    * The Events API and Change Events APIs only accept POST.
    """

    retry = {}
    """
    A dict defining the retry behavior for each HTTP response status code.

    Each key in this dictionary is an int representing a HTTP response code. The
    behavior is specified by the int value at each key as follows:

    * ``-1`` to retry without limit.
    * ``0`` has no effect; the default behavior will take effect.
    * ``n``, where ``n > 0``, to retry ``n`` times (or up
      to :attr:`max_http_attempts` total for all statuses, whichever is
      encountered first), and then return the final response.

    The default behavior is to retry without limit on status 429, raise an
    exception on a 401, and return the `requests.Response`_ object in any other case
    (assuming a HTTP response was received from the server).
    """

    sleep_timer = 1.5
    """
    Default initial cooldown time factor for rate limiting and network errors.

    Each time that the request makes a followup request, there will be a delay
    in seconds equal to this number times :attr:`sleep_timer_base` to the power
    of how many attempts have already been made so far, unless
    :attr:`stagger_cooldown` is nonzero.
    """

    sleep_timer_base = 2
    """
    After each retry, the time to sleep before reattempting the API connection
    and request will increase by a factor of this amount.
    """

    timeout = TIMEOUT
    """
    This is the value sent to `Requests`_ as the ``timeout`` parameter that
    determines the TCP read timeout.
    """

    url = ""
    """
    The base URL for the API being called (usually https://api.pagerduty.com, but
    this can vary depending on the specific API being accessed).
    """

    def __init__(self, auth_method: AuthMethod, debug=False):
        self.parent = super(ApiClient, self)
        self.parent.__init__()
        self.auth_method = auth_method
        self.log = logging.getLogger(__name__)
        self.print_debug = debug
        self.retry = {}

    def after_set_auth_method(self):
        """
        Setter hook for setting or updating the authentication method.
        Child classes should implement this to perform additional steps.
        """
        pass

    @property
    def auth_method(self) -> AuthMethod:
        """
        Property representing the authentication method used for API requests.
        """
        return self._auth_method

    @auth_method.setter
    def auth_method(self, auth_method: AuthMethod):
        if not (isinstance(auth_method, AuthMethod)):
            raise ValueError("auth_method must be an instance of the AuthMethod class")

        self._auth_method = auth_method
        self.after_set_auth_method()

    @property
    def auth_header(self) -> dict:
        """
        Generates the Authorization header based on auth_method provided.
        """
        warn("Property ApiClient.auth_header is deprecated. " +
            "Use ApiClient.auth_method.auth_header instead.")
        return self.auth_method.auth_header

    def cooldown_factor(self) -> float:
        return self.sleep_timer_base*(1+self.stagger_cooldown*random())

    def normalize_params(self, params: dict) -> dict:
        """
        Modify the user-supplied parameters to ease implementation

        :returns:
            The query parameters after modification
        """
        return params

    def normalize_url(self, url: str) -> str:
        """Compose the URL whether it is a path or an already-complete URL"""
        return normalize_url(self.url, url)

    def postprocess(self, response: Response):
        """
        Perform supplemental actions immediately after receiving a response.

        This method is called once per request not including retries, and can be
        extended in child classes.
        """
        pass

    def prepare_headers(self, method: str, user_headers: Optional[dict] = None) -> dict:
        """
        Append special additional per-request headers.

        :param method:
            The HTTP method, in upper case.
        :param user_headers:
            Headers that can be specified to override default values.
        :returns:
            The final list of headers to use in the request
        """
        # Utilize any defaults that the implementer has set via the upstream interface:
        headers = deepcopy(self.headers)
        # Override the default user-agent with the per-class user_agent property:
        headers['User-Agent'] = self.user_agent
        # A universal convention: whenever sending a POST, PUT or PATCH, the
        # Content-Type header must be "application/json":
        if method in ('POST', 'PUT', 'PATCH'):
            headers['Content-Type'] = 'application/json'
        # Add headers passed in per-request as an additional argument:
        if type(user_headers) is dict:
            headers.update(user_headers)
        # Add authentication header, if the auth_method defines it:
        headers.update(self.auth_method.auth_header)
        return headers

    @property
    def print_debug(self) -> bool:
        """
        Printing debug flag

        If set to True, the logging level of :attr:`log` is set to
        ``logging.DEBUG`` and all log messages are emitted to ``sys.stderr``.
        If set to False, the logging level of :attr:`log` is set to
        ``logging.NOTSET`` and the debugging log handler that prints messages to
        ``sys.stderr`` is removed. This value thus can be toggled to enable and
        disable verbose command line output.

        It is ``False`` by default and it is recommended to keep it that way in
        production settings.
        """
        return self._debug

    @print_debug.setter
    def print_debug(self, debug: bool):
        self._debug = debug
        if debug and not hasattr(self, '_debugHandler'):
            self.log.setLevel(logging.DEBUG)
            self._debugHandler = logging.StreamHandler()
            self.log.addHandler(self._debugHandler)
        elif not debug and hasattr(self, '_debugHandler'):
            self.log.setLevel(logging.NOTSET)
            self.log.removeHandler(self._debugHandler)
            delattr(self, '_debugHandler')
        # else: no-op; only happens if debug is set to the same value twice

    def request(self, method: str, url: str, **kwargs) -> Response:
        """
        Make a generic PagerDuty API request.

        :param method:
            The request method to use. Case-insensitive. May be one of get, put,
            post or delete.
        :param url:
            The path/URL to request. If it does not start with the base URL, the
            base URL will be prepended.
        :param **kwargs:
            Custom keyword arguments to pass to ``requests.Session.request``.
        :type method: str
        :type url: str
        :returns:
            The `requests.Response`_ object corresponding to the HTTP response
        """
        sleep_timer = self.sleep_timer
        network_attempts = 0
        http_attempts = {}
        method = method.strip().upper()
        if method not in self.permitted_methods:
            m_str = ', '.join(self.permitted_methods)
            raise Error(f"Method {method} not supported by this API. " \
                f"Permitted methods: {m_str}")
        req_kw = deepcopy(kwargs)
        full_url = self.normalize_url(url)
        endpoint = "%s %s"%(method.upper(), full_url)

        # Add in any headers specified in keyword arguments:
        headers = kwargs.get('headers', {})
        req_kw.update({
            'headers': self.prepare_headers(method, user_headers=headers),
            'stream': False,
            'timeout': self.timeout
        })

        # Add authentication parameter, if the API requires it and it is a request type
        # that includes a body:
        if method in ('POST', 'PUT', 'PATCH'):
            for body_key in ('json', 'data'):
                if body_key in req_kw and type(req_kw[body_key]) is dict:
                    req_kw[body_key].update(self.auth_method.auth_param)

        # Special changes to user-supplied query parameters, for convenience:
        if 'params' in kwargs and kwargs['params']:
            req_kw['params'] = self.normalize_params(kwargs['params'])

        # Make the request (and repeat w/cooldown if the rate limit is reached):
        while True:
            try:
                response = self.parent.request(method, full_url, **req_kw)
                self.postprocess(response)
            except (Urllib3HttpError, PoolError, RequestException) as e:
                network_attempts += 1
                if network_attempts > self.max_network_attempts:
                    error_msg = f"{endpoint}: Non-transient network " \
                        'error; exceeded maximum number of attempts ' \
                        f"({self.max_network_attempts}) to connect to the API."
                    raise Error(error_msg) from e
                sleep_timer *= self.cooldown_factor()
                self.log.warning(
                    "%s: HTTP or network error: %s. retrying in %g seconds.",
                    endpoint, e.__class__.__name__, sleep_timer)
                time.sleep(sleep_timer)
                continue

            status = response.status_code
            retry_logic = self.retry.get(status, 0)
            if not response.ok and retry_logic != 0:
                # Take special action as defined by the retry logic
                if retry_logic != -1:
                    # Retry a specific number of times (-1 implies infinite)
                    if http_attempts.get(status, 0)>=retry_logic or \
                            sum(http_attempts.values())>self.max_http_attempts:
                        lower_limit = retry_logic
                        if lower_limit > self.max_http_attempts:
                            lower_limit = self.max_http_attempts
                        self.log.error(
                            f"%s: Non-transient HTTP error: exceeded " \
                            'maximum number of attempts (%d) to make a ' \
                            'successful request. Currently encountering ' \
                            'status %d.', endpoint, lower_limit, status)
                        return response
                    http_attempts[status] = 1 + http_attempts.get(status, 0)
                sleep_timer *= self.cooldown_factor()
                self.log.warning("%s: HTTP error (%d); retrying in %g seconds.",
                    endpoint, status, sleep_timer)
                time.sleep(sleep_timer)
                continue
            elif status == 429:
                sleep_timer *= self.cooldown_factor()
                self.log.debug("%s: Hit API rate limit (status 429); " \
                    "retrying in %g seconds", endpoint, sleep_timer)
                time.sleep(sleep_timer)
                continue
            elif status == 401:
                # Stop. Authentication failed. We shouldn't try doing any more,
                # because we'll run into the same problem later anyway.
                raise HttpError(
                    "Received 401 Unauthorized response from the API. The key "
                    "(...%s) may be invalid or deactivated."%self.trunc_key,
                    response)
            else:
                # All went according to plan.
                return response

    @property
    def stagger_cooldown(self) -> float:
        """
        Randomizing factor for wait times between retries during rate limiting.

        If set to number greater than 0, the sleep time for rate limiting will
        (for each successive sleep) be adjusted by a factor of one plus a
        uniformly-distributed random number between 0 and 1 times this number,
        on top of the base sleep timer :attr:`sleep_timer_base`.

        For example:

        * If this is 1, and :attr:`sleep_timer_base` is 2 (default), then after
          each status 429 response, the sleep time will change overall by a
          random factor between 2 and 4, whereas if it is zero, it will change
          by a factor of 2.
        * If :attr:`sleep_timer_base` is 1, then the cooldown time will be
          adjusted by a random factor between one and one plus this number.

        If the number is set to zero, then this behavior is effectively
        disabled, and the cooldown factor (by which the sleep time is adjusted)
        will just be :attr:`sleep_timer_base`

        Setting this to a nonzero number helps avoid the "thundering herd"
        effect that can potentially be caused by many API clients making
        simultaneous concurrent API requests and consequently waiting for the
        same amount of time before retrying.  It is currently zero by default
        for consistent behavior with previous versions.
        """
        if hasattr(self, '_stagger_cooldown'):
            return self._stagger_cooldown
        else:
            return 0

    @stagger_cooldown.setter
    def stagger_cooldown(self, val: Union[float, int]):
        if type(val) not in [float, int] or val<0:
            raise ValueError("Cooldown randomization factor stagger_cooldown "
                "must be a positive real number")
        self._stagger_cooldown = val

    @property
    def trunc_key(self) -> str:
        """Truncated key for secure display/identification purposes."""
        return self.auth_method.trunc_secret

    @property
    def user_agent(self) -> str:
        return 'python-pagerduty/%s python-requests/%s Python/%d.%d'%(
            __version__,
            REQUESTS_VERSION,
            sys.version_info.major,
            sys.version_info.minor
        )


