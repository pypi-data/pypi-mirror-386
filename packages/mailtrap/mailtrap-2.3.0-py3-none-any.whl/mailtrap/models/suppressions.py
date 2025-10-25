from datetime import datetime
from enum import Enum
from typing import Optional
from typing import Union

from pydantic.dataclasses import dataclass


class SuppressionType(str, Enum):
    HARD_BOUNCE = "hard bounce"
    SPAM_COMPLAINT = "spam complaint"
    UNSUBSCRIPTION = "unsubscription"
    MANUAL_IMPORT = "manual import"


class SendingStream(str, Enum):
    TRANSACTIONAL = "transactional"
    BULK = "bulk"


@dataclass
class Suppression:
    id: str
    type: SuppressionType
    created_at: datetime
    email: str
    sending_stream: SendingStream
    domain_name: Optional[str] = None
    message_bounce_category: Optional[str] = None
    message_category: Optional[str] = None
    message_client_ip: Optional[str] = None
    message_created_at: Optional[Union[str, datetime]] = None
    message_esp_response: Optional[str] = None
    message_esp_server_type: Optional[str] = None
    message_outgoing_ip: Optional[str] = None
    message_recipient_mx_name: Optional[str] = None
    message_sender_email: Optional[str] = None
    message_subject: Optional[str] = None
