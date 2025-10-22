from dataclasses import dataclass, field
from uuid import uuid4
import logging

logger = logging.getLogger()


@dataclass
class MessageData:

    payload: dict
    message_id: str = None
    request_id: str = None

    def toDict(self):
        return self.__dict__

    def __post_init__(self):
        self.message_id = uuid4().hex + uuid4().hex
        if self.request_id is None:
            self.request_id = uuid4().hex + uuid4().hex


@dataclass
class Method:

    consumer_tag: str
    exchange: str
    routing_key: str