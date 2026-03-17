"""
Tip-gÃ¼venli event sÃ¶zleÅŸmeleri ve versiyon bilgisi.
Producer/consumer tarafÄ± aynÄ± ÅŸemayÄ± kullanmalÄ±.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    TRIP_CREATED = "trip.created"
    FUEL_UPDATED = "fuel.updated"
    MODEL_RETRAIN_REQUESTED = "ml.retrain.requested"


class BaseEvent(BaseModel):
    event_id: str = Field(..., description="UUID4 â€” idempotency iÃ§in zorunlu")
    event_type: EventType
    version: str = "1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


class TripCreatedEvent(BaseEvent):
    payload: dict


class FuelUpdatedEvent(BaseEvent):
    payload: dict


class ModelRetrainRequestedEvent(BaseEvent):
    payload: dict


__all__ = [
    "EventType",
    "BaseEvent",
    "TripCreatedEvent",
    "FuelUpdatedEvent",
    "ModelRetrainRequestedEvent",
]
