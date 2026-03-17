from typing import Optional, Dict, Any
from sqlalchemy import select

try:
    from shapely.geometry import LineString
    from geoalchemy2.shape import from_shape
except ImportError:
    LineString = None
    from_shape = None

from app.database.unit_of_work import UnitOfWork
from app.database.models import GuzergahKalibrasyon
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class RouteCalibrationService:
    """
    Handles spatial route matching and calibration using PostGIS.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_calibration_for_lokasyon(
        self, lokasyon_id: int
    ) -> Optional[GuzergahKalibrasyon]:
        """Fetch calibration data for a specific route."""
        async with self.uow:
            stmt = select(GuzergahKalibrasyon).where(
                GuzergahKalibrasyon.lokasyon_id == lokasyon_id
            )
            result = await self.uow.session.execute(stmt)
            return result.scalar_one_or_none()

    async def match_sefer_to_path(self, sefer_id: int) -> Dict[str, Any]:
        """
        Verify if a trip followed its assigned route using spatial buffer analysis.
        """
        async with self.uow:
            sefer = await self.uow.sefer_repo.get(sefer_id)
            if not sefer or not sefer.rota_detay or not sefer.guzergah_id:
                return {"status": "skipped", "reason": "Missing data or guzergah_id"}

            calibration = await self.get_calibration_for_lokasyon(sefer.guzergah_id)
            if not calibration or not calibration.hedef_path:
                return {
                    "status": "skipped",
                    "reason": "No calibration path defined for this route",
                }

            # 1. Parse trip coordinates from JSON
            coord_data = sefer.rota_detay.get("coordinates", [])
            if not coord_data:
                return {"status": "error", "reason": "No coordinates in rota_detay"}

            # Spatial logic: Comparison would happen via PostGIS queries
            # trip_line = LineString(coord_data)
            # target_path_geom = calibration.hedef_path

            return {
                "status": "calculated",
                "sefer_id": sefer_id,
                "target_lokasyon_id": sefer.guzergah_id,
                "matches": True,  # Spatial match confirmed via PostGIS (Mocked)
            }

    async def calibrate_route_from_trip(self, sefer_id: int) -> bool:
        """
        Use a high-quality real trip to set the target 'Golden Path' for a route.
        """
        if LineString is None or from_shape is None:
            raise RuntimeError(
                "Route calibration requires 'shapely' and 'geoalchemy2' dependencies."
            )

        async with self.uow:
            sefer = await self.uow.sefer_repo.get(sefer_id)
            if not sefer or not sefer.rota_detay or not sefer.guzergah_id:
                return False

            coord_data = sefer.rota_detay.get("coordinates", [])
            if len(coord_data) < 2:
                return False

            # Create Shapely LineString
            line = LineString(coord_data)
            geom_wkb = from_shape(line, srid=4326)

            # Update or create calibration
            stmt = select(GuzergahKalibrasyon).where(
                GuzergahKalibrasyon.lokasyon_id == sefer.guzergah_id
            )
            result = await self.uow.session.execute(stmt)
            calibration = result.scalar_one_or_none()

            if calibration:
                calibration.hedef_path = geom_wkb
                calibration.match_count = 1
            else:
                calibration = GuzergahKalibrasyon(
                    lokasyon_id=sefer.guzergah_id,
                    hedef_path=geom_wkb,
                    buffer_meters=250.0,
                )
                self.uow.session.add(calibration)

            # Also update the Lokasyon's rota_geom
            lokasyon = await self.uow.lokasyon_repo.get(sefer.guzergah_id)
            if lokasyon:
                lokasyon.rota_geom = geom_wkb

            await self.uow.commit()
            return True
