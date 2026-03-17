import pytest

from app.infrastructure.events.event_bus import EventBus, EventType, Event


def setup_bus():
    bus = EventBus()
    bus._processed_events.clear()
    bus._failed_events.clear()
    bus._event_history.clear()
    return bus


def test_dedup_in_memory():
    bus = setup_bus()
    counter = {"called": 0}

    def handler(evt: Event):
        counter["called"] += 1

    bus.subscribe(EventType.SEFER_ADDED, handler)
    evt = Event(type=EventType.SEFER_ADDED, event_id="fixed-id", data={"x": 1})
    bus.publish(evt)
    bus.publish(evt)  # duplicate

    assert counter["called"] == 1


def test_dlq_on_failure():
    bus = setup_bus()

    def boom(evt: Event):
        raise RuntimeError("boom")

    bus.subscribe(EventType.SEFER_ADDED, boom)
    evt = Event(type=EventType.SEFER_ADDED, event_id="dlq-test")
    bus.publish(evt)

    assert bus._failed_events, "DLQ should record failed event"
    last = bus._failed_events[-1]
    assert last[0].event_id == "dlq-test"
    assert "boom" in last[2]
