from app.infrastructure.events.event_bus import Event, EventType, get_event_bus
from app.infrastructure.logging.logger import get_logger
from app.database.unit_of_work import UnitOfWork

logger = get_logger(__name__)


async def handle_fuel_added(event: Event):
    """
    Yakıt eklendiğinde ilgili seferleri bul ve tüketimi KM ağırlıklı dağıt.
    (Smart Reconciliation Strategy)
    """
    yakit_id = event.data.get("result")
    if not yakit_id:
        return

    logger.info(f"Handling Fuel Added Event (Smart Reconcile) for YakitID: {yakit_id}")

    async with UnitOfWork() as uow:
        # 1. Get Fuel Record
        yakit = await uow.yakit_repo.get_by_id(yakit_id)
        if not yakit:
            logger.warning(f"Fuel record {yakit_id} not found during event handling.")
            return

        fuel_liters = float(yakit["litre"])
        logger.info(
            f"Processing Fuel: {fuel_liters}L for Vehicle {yakit['arac_id']} on {yakit['tarih']}"
        )

        # 2. Find ALL Matching Trips (Same Vehicle, Same Date)
        trips = await uow.sefer_repo.get_all(
            filters={"arac_id": yakit["arac_id"], "tarih": yakit["tarih"]}
        )

        if not trips:
            logger.info(
                f"No trip found for Vehicle {yakit['arac_id']} on {yakit['tarih']}. Consumption not assigned."
            )
            return

        # 3. Calculate Total Distance for the Day
        total_daily_km = sum(t["mesafe_km"] for t in trips if t.get("mesafe_km"))

        if total_daily_km <= 0:
            logger.warning(
                f"Total distance is 0 for {len(trips)} trips. Cannot distribute fuel."
            )
            return

        logger.info(
            f"Found {len(trips)} trips. Total Distance: {total_daily_km}km. Distributing {fuel_liters}L..."
        )

        # 4. Distribute Fuel Weighted by Distance
        for trip_data in trips:
            trip_id = trip_data["id"]
            trip_km = trip_data.get("mesafe_km", 0)

            if trip_km <= 0:
                continue

            # Weight factor: TripKM / TotalDailyKM
            ratio = trip_km / total_daily_km
            allocated_liters = fuel_liters * ratio

            # Consumption (L/100km): (AllocatedLiters / TripKM) * 100
            # Math simplification: (Fuel * (Trip/Total)) / Trip * 100
            #                   = (Fuel / Total) * 100
            # So consumption rate is identical for all trips that day, which makes sense physically
            # (average daily consumption), but allocated liters differs.

            consumption = (allocated_liters / trip_km) * 100

            logger.info(
                f" -> Trip {trip_id} ({trip_km}km, Ratio {ratio:.2f}): "
                f"Allocated {allocated_liters:.2f}L, Rate {consumption:.2f} L/100km"
            )

            # Update Trip
            await uow.sefer_repo.update(
                trip_id,
                tuketim=consumption,
                dagitilan_yakit=allocated_liters,
                durum="Tamam",  # Auto-complete
            )

            # Publish update event for each trip
            # Note: We fire simple async events to avoid blocking loop
            await get_event_bus().publish_simple_async(
                EventType.SEFER_UPDATED, id=trip_id, tuketim=consumption
            )

        # Commit all changes
        await uow.commit()
        logger.info("Smart Fuel Distribution Completed.")


def register_fuel_handlers():
    """Register handlers to EventBus"""
    bus = get_event_bus()
    bus.subscribe(EventType.YAKIT_ADDED, handle_fuel_added)

    # Phase 2: New Elite Handlers
    from app.core.services.anomaly_handler import register_anomaly_handlers
    from app.core.services.period_handler import register_period_handlers

    register_anomaly_handlers()
    register_period_handlers()

    logger.info("Fuel Event Handlers Registered (with Anomaly & Period support).")
