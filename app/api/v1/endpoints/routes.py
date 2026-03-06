from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import SessionDep, get_current_user
from app.database.models import Kullanici
from app.services.route_service import RouteService

router = APIRouter()


class RouteAnalysisRequest(BaseModel):
    start_lat: float = Field(..., ge=-90, le=90)
    start_lon: float = Field(..., ge=-180, le=180)
    end_lat: float = Field(..., ge=-90, le=90)
    end_lon: float = Field(..., ge=-180, le=180)


@router.post("/analyze")
async def analyze_route(
    request: RouteAnalysisRequest,
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
):
    service = RouteService()

    start_coords = (request.start_lon, request.start_lat)
    end_coords = (request.end_lon, request.end_lat)

    result = await service.get_route_details(start_coords, end_coords)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # Add difficulty analysis
    difficulty = service.analyze_route_difficulty(
        result.get("ascent_m", 0),
        result.get("descent_m", 0),
        result.get("distance_km", 0),
    )

    result["difficulty"] = difficulty
    return result
