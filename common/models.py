from pydantic import BaseModel, Field
from typing import Dict, Optional
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CHECKOUT_INITIATED = "CHECKOUT_INITIATED"
    INVENTORY_RESERVED = "INVENTORY_RESERVED"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    SHIPPING_STARTED = "SHIPPING_STARTED"
    ORDER_COMPLETED = "ORDER_COMPLETED"
    FAILED = "FAILED"

class OrderEvent(BaseModel):
    order_id: str
    correlation_id: str
    customer_id: str
    total_amount: float
    status: OrderStatus = OrderStatus.PENDING
    payload: Dict[str, str] = Field(default_factory=dict)

class InventoryReply(BaseModel):
    order_id: str
    status: str
    reason: Optional[str] = None
