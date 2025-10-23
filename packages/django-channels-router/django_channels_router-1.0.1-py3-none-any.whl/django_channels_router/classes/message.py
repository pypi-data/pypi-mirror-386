from typing import Any, Self

from .status import StatusCodes


class BaseMessage:
    """
    This class provides the Abstract type of Message with required fields and methods
    that the library highly depends on them.
    """

    """
    route is used to determine which method is responsible to handle the incoming message
    the routes will convert to snakecase for making method names.
    method names will follow this: f"on_{snakecase(route)}"
    """
    _route: str
    """
    uuid acts as a tracking code, so that when server responses the client with this code,
    the client will identify which request does it belongs to. another essential part of this
    library.
    """
    _uuid: str | int
    """
    While there aren't actual headers part when using socket as transition protocol, to make it feel more like http call
    this field is added, I found it meaningful to send metadata(like API_KEY or even entity ID) through headers and use payload to send actual data 
    """
    _headers: dict | None = None
    """
    Payload field is designed to be used as main data storage. It's supposed to mostly contain a dictionary (the message
    object itself is Json coded and decoded so the rest data are not Json Coded), however any other value is possible
    like string, int, float, even a simple boolean or a huge base64 encoded string.
    """
    _payload: Any = None
    """
    Status Field is supposed to be set for sending responses, just like HTTP calls.
    """
    _status: int = StatusCodes.OK

    @property
    def route(self) -> str:
        return self._route

    @property
    def uuid(self) -> str | int:
        return self._uuid

    @property
    def headers(self) -> dict:
        return self._headers

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, value):
        self._payload = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status: int):
        self._status = status

    def __init__(
            self,
            route: str,
            uuid: str | int,
            headers: dict[str, str] | None = None,
            payload: Any = None,
            status: int = StatusCodes.OK
    ):
        self._route = route
        self._uuid = uuid
        self._headers = headers
        self._payload = payload
        self._status = status

    @classmethod
    def from_incoming_message(cls, incoming_message: dict):
        uuid = incoming_message.get('uuid')
        if not uuid or not isinstance(uuid, str):
            raise KeyError("uuid is missing or wrong format")
        route = incoming_message.get('route')
        if not route or not isinstance(route, str):
            raise KeyError("proper route is missing")

        headers = incoming_message.get('headers')
        headers = headers if isinstance(headers, dict) else None
        payload = incoming_message.get('payload')
        message = BaseMessage(route=route, uuid=uuid, headers=headers, payload=payload)
        return message

    @classmethod
    def build_response(cls, income_message: Self, headers: dict[str,str] | None = None,payload: Any = None, status: int = StatusCodes.OK):
        return BaseMessage(income_message.route, income_message.uuid, headers, payload, status)

    def serialize(self) -> dict:
        return {
            'uuid': self.uuid,
            'route': self.route,
            'headers': self.headers,
            'payload': self.payload,
            'status': self.status
        }