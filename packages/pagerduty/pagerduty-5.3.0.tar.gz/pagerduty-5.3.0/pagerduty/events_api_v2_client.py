# Core
from copy import deepcopy
from datetime import datetime
from typing import (
    List,
    Optional
)

# PyPI
from requests import Response

# Local
from . api_client import ApiClient
from . auth_method import BodyParameterAuthMethod
from . common import (
    deprecated_kwarg,
    successful_response,
    try_decoding,
    truncate_text,
    last_4
)

class RoutingKeyAuthMethod(BodyParameterAuthMethod):
    """
    AuthMethod for Events API V2, which requires a ``routing_key`` parameter be set in
    the request body.
    """
    @property
    def auth_param(self) -> dict:
        return {"routing_key": self.secret}

class EventsApiV2Client(ApiClient):

    """
    Session class for submitting events to the PagerDuty v2 Events API.

    Implements methods for submitting events to PagerDuty through the Events API,
    including change events, and inherits from :class:`pagerduty.ApiClient`.  For more
    details on usage of this API, refer to the `Events API v2 documentation
    <https://developer.pagerduty.com/docs/events-api-v2/overview/>`_

    :param routing_key:
        The routing key to use for authentication with the Events API. Sometimes called
        an ``integration_key`` or ``service_key`` in legacy integrations.

    :param debug:
        Sets :attr:`pagerduty.ApiClient.print_debug`. Set to ``True`` to enable verbose
        command line output.
    """

    permitted_methods = ('POST',)

    url = "https://events.pagerduty.com"

    def __init__(self, routing_key: str, debug: bool = False):
        auth_method = RoutingKeyAuthMethod(routing_key)
        super(EventsApiV2Client, self).__init__(auth_method, debug)
        # See: https://developer.pagerduty.com/docs/3d063fd4814a6-events-api-v2-overview#response-codes--retry-logic
        self.retry[500] = 2 # internal server error
        self.retry[502] = 4 # bad gateway
        self.retry[503] = 6 # service unavailable
        self.retry[504] = 6 # gateway timeout

    def acknowledge(self, dedup_key: str) -> str:
        """
        Acknowledge an alert via Events API.

        :param dedup_key:
            The deduplication key of the alert to set to the acknowledged state.
        :returns:
            The deduplication key
        """
        return self.send_event('acknowledge', dedup_key=dedup_key)

    @property
    def event_timestamp(self) -> str:
        return datetime.utcnow().isoformat()+'Z'

    def resolve(self, dedup_key: str) -> str:
        """
        Resolve an alert via Events API.

        :param dedup_key:
            The deduplication key of the alert to resolve.
        """
        return self.send_event('resolve', dedup_key=dedup_key)

    def send_change_event(self, payload: Optional[dict] = None,
                links: Optional[List[dict]] = None,
                routing_key: Optional[str] = None,
                images: Optional[List[dict]] = None):
        """
        Send a change event to the v2 Change Events API.

        See: https://developer.pagerduty.com/docs/events-api-v2/send-change-events/

        :param payload:
            A dictionary object with keys ``summary``, ``source``, ``timestamp`` and
            ``custom_details`` as described in the above documentation.
        :param links:
            A list of dictionary objects each with keys ``href`` and ``text``
            representing the target and display text of each link
        :param routing_key:
            (Deprecated) the routing key. This parameter should be set via the
            constructor `routing_key` parameter instead -- this argument is ignored.
        :param images:
            Optional list of images to attach to the change event.
        """
        if payload is None:
            payload = {}
        if links is None:
            links = []
        if images is None:
            images = []
        if routing_key is not None:
            deprecated_kwarg(
                'routing_key',
                method='EventsApiV2Client.send_change_event'
            )
        event = {'payload': deepcopy(payload)}
        if links:
            event['links'] = deepcopy(links)
        if images:
            event['images'] = deepcopy(images)
        successful_response(
            self.post('/v2/change/enqueue', json=event),
            context="submitting change event",
        )

    def send_event(self, action: str, dedup_key: Optional[str] = None, **properties) \
            -> str:
        """
        Send an event to the v2 Events API.

        See: https://v2.developer.pagerduty.com/docs/send-an-event-events-api-v2

        :param action:
            The action to perform through the Events API: trigger, acknowledge
            or resolve.
        :param dedup_key:
            The deduplication key; used for determining event uniqueness and
            associating actions with existing incidents.
        :param **properties:
            Additional properties to set, i.e. if ``action`` is ``trigger``
            this would include ``payload``.
        :type action: str
        :type dedup_key: str
        :returns:
            The deduplication key of the incident
        """

        actions = ('trigger', 'acknowledge', 'resolve')
        if action not in actions:
            raise ValueError("Event action must be one of: "+', '.join(actions))

        event = {'event_action':action}

        event.update(properties)
        if isinstance(dedup_key, str):
            event['dedup_key'] = dedup_key
        elif not action == 'trigger':
            raise ValueError("The dedup_key property is required for"
                "event_action=%s events, and it must be a string."%action)
        response = successful_response(
            self.post('/v2/enqueue', json=event),
            context='submitting an event to the events API',
        )
        response_body = try_decoding(response)
        if type(response_body) is not dict or 'dedup_key' not in response_body:
            err_msg = 'Malformed response body from the events API; it is ' \
                'not a dict that has a key named "dedup_key" after ' \
                'decoding. Body = '+truncate_text(response.text)
            raise ServerHttpError(err_msg, response)
        return response_body['dedup_key']

    def submit(self, summary: str, source: Optional[str] = None,
                custom_details: Optional[dict] = None,
                links: Optional[List[dict]] = None,
                timestamp: Optional[str] = None):
        """
        Submit a change event.

        See: https://developer.pagerduty.com/docs/send-change-event

        This is a wrapper method for :attr:`send_change_event` that composes an event
        payload from keyword arguments and an auto-generated event timestamp. To send an
        event with a wholly custom payload, use :attr:`send_change_event` instead.

        :param summary:
            Summary / brief description of the change, for ``payload.summary``.
        :param source:
            A human-readable name identifying the source of the change, for the
            ``payload.source`` event property.
        :param custom_details:
            A dictionary object to use as the ``payload.custom_details`` property.
        :param links:
            A list of dict objects to use as the ``links`` property of the event.
        :param timestamp:
            Specifies an event timestamp. Must be an ISO8601-format date/time.
        :type summary: str
        :type source: str
        :type custom_details: dict
        :type links: list
        :type timestamp: str
        """
        local_var = locals()['custom_details']
        if not (local_var is None or isinstance(local_var, dict)):
            raise ValueError("custom_details must be a dict")
        if timestamp is None:
            timestamp = self.event_timestamp
        event = {
                'payload': {
                    'summary': summary,
                    'timestamp': timestamp,
                    }
                }
        if isinstance(source, str):
            event['payload']['source'] = source
        if isinstance(custom_details, dict):
            event['payload']['custom_details'] = custom_details
        if links:
            event['links'] = links
        self.send_change_event(**event)

    def trigger(self, summary: str, source: str, dedup_key: Optional[str] = None, \
                severity: str = 'critical', payload: Optional[str] = None, \
                custom_details: Optional[dict] = None,
                images: Optional[List[dict]] = None,
                links: Optional[List[dict]] = None) -> str:
        """
        Send an alert-triggering event

        :param summary:
            Summary / brief description of what is wrong.
        :param source:
            A human-readable name identifying the system that is affected.
        :param dedup_key:
            The deduplication key; used for determining event uniqueness and
            associating actions with existing incidents.
        :param severity:
            Alert severity. Sets the ``payload.severity`` property.
        :param payload:
            Set the payload directly. Can be used in conjunction with other
            parameters that also set payload properties; these properties will
            be merged into the default payload, and any properties in this
            parameter will take precedence except with regard to
            ``custom_details``.
        :param custom_details:
            The ``payload.custom_details`` property of the payload. Will
            override the property set in the ``payload`` parameter if given.
        :param images:
            Set the ``images`` property of the event.
        :param links:
            Set the ``links`` property of the event.
        :type action: str
        :type custom_details: dict
        :type dedup_key: str
        :type images: list
        :type links: list
        :type payload: dict
        :type severity: str
        :type source: str
        :type summary: str
        :returns:
            The deduplication key of the incident, if any.
        """
        for local in ('payload', 'custom_details'):
            local_var = locals()[local]
            if not (local_var is None or type(local_var) is dict):
                raise ValueError(local+" must be a dict")
        event = {'payload': {'summary':summary, 'source':source,
            'severity':severity}}
        if type(payload) is dict:
            event['payload'].update(payload)
        if type(custom_details) is dict:
            details = event.setdefault('payload', {}).get('custom_details', {})
            details.update(custom_details)
            event['payload']['custom_details'] = details
        if images:
            event['images'] = images
        if links:
            event['links'] = links
        return self.send_event('trigger', dedup_key=dedup_key, **event)

