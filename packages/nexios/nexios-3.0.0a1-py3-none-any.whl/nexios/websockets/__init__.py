import typing

from .base import WebSocket, WebSocketDisconnect  # type:ignore
from .channels import Channel, ChannelBox
from .consumers import WebSocketConsumer

Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]

Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]


__all__ = [
    "WebSocket",
    "Channel",
    "ChannelBox",
    "WebSocketConsumer",
    "WebSocketDisconnect",
]
