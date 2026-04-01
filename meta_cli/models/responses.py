from typing import Any, List, Optional

from pydantic import BaseModel


class App(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None


class AppsResponse(BaseModel):
    data: List[App]


class PhoneNumber(BaseModel):
    id: str
    display_phone_number: str
    verified_name: Optional[str] = None
    quality_rating: Optional[str] = None
    status: Optional[str] = None


class PhoneNumbersResponse(BaseModel):
    data: List[PhoneNumber]


class MessageTemplate(BaseModel):
    id: str
    name: str
    status: str
    category: str
    language: Optional[str] = None


class TemplatesResponse(BaseModel):
    data: List[MessageTemplate]


class SendMessageContact(BaseModel):
    input: str
    wa_id: str


class SendMessageResult(BaseModel):
    id: str
    message_status: Optional[str] = None


class SendMessageResponse(BaseModel):
    messaging_product: str
    contacts: List[SendMessageContact]
    messages: List[SendMessageResult]


class MeResponse(BaseModel):
    id: str
    name: Optional[str] = None


class GraphError(BaseModel):
    message: str
    type: str
    code: int
    error_subcode: Optional[int] = None
    fbtrace_id: Optional[str] = None


class WebhookSubscriptionResponse(BaseModel):
    success: Optional[bool] = None
    id: Optional[str] = None
    data: Optional[List[Any]] = None
