from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MenuItem(BaseModel):
    id: int
    name: str
    category: str
    price: int = Field(description="가격 (원)")
    available: bool = True


class OrderLineIn(BaseModel):
    menu_id: int
    quantity: int = Field(ge=1, le=99)


class OrderIn(BaseModel):
    items: list[OrderLineIn] = Field(min_length=1)


class OrderLine(BaseModel):
    menu_id: int
    name: str
    unit_price: int
    quantity: int
    subtotal: int


class OrderStatus(str, Enum):
    RECEIVED = "received"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(BaseModel):
    id: int
    number: int = Field(description="고객 호출 번호")
    items: list[OrderLine]
    total: int
    status: OrderStatus = OrderStatus.RECEIVED
    created_at: datetime


class StatusUpdate(BaseModel):
    status: OrderStatus
