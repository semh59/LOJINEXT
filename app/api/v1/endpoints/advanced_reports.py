"""
LojiNext AI - Gelişmiş Raporlama API Endpoint'leri
PDF raporlar ve maliyet analizi
"""

import asyncio
import io
from datetime import date, datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.api.deps import SessionDep, get_current_user
from app.core.services.cost_analyzer import get_cost_analyzer
from app.core.services.export_service import get_export_service
from app.core.services.report_generator import get_report_generator
from app.core.services.report_service import get_report_service
from app.database.models import Kullanici

router = APIRouter()


class CostBreakdownResponse(BaseModel):
    fuel_cost: float
    fuel_liters: float
    avg_price_per_liter: float
    trip_count: int
    total_distance: float
    cost_per_km: float
    period_start: str
    period_end: str


class SavingsPotentialResponse(BaseModel):
    current_consumption: float
    target_consumption: float
    current_cost: float
    target_cost: float
    potential_savings: float
    savings_percentage: float
    annual_projection: float


class ROIResponse(BaseModel):
    investment: float
    monthly_savings: float
    annual_savings: float
    payback_months: float
    annual_roi_percentage: float
    cost_improvement_pct: float


@router.get("/pdf/fleet-summary")
async def get_fleet_summary_pdf(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """
    Filo özet raporu PDF olarak indir

    Args:
        start_date: Başlangıç tarihi (YYYY-MM-DD)
        end_date: Bitiş tarihi (YYYY-MM-DD)
    """
    try:
        # Tarih parsing
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start = date.today() - timedelta(days=30)

        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end = date.today()

        # Rapor verileri (async)
        report_service = get_report_service()
        data = await report_service.generate_fleet_summary(start, end)

        # PDF oluştur (Bloklayıcı işlemi thread'e taşı)
        generator = get_report_generator()
        pdf_bytes = await asyncio.to_thread(
            generator.generate_fleet_summary, start, end, data
        )

        # Response
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=filo_ozet_{start}_{end}.pdf"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pdf/vehicle/{arac_id}")
async def get_vehicle_report_pdf(
    arac_id: int,
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2100),
):
    """
    Araç detay raporu PDF olarak indir

    Args:
        arac_id: Araç ID
        month: Ay (1-12)
        year: Yıl (2020-2100)
    """
    try:
        # Rapor verileri (async)
        report_service = get_report_service()
        data = await report_service.generate_vehicle_report(arac_id, month, year)

        if not data or "error" in data:
            raise HTTPException(status_code=404, detail="Araç bulunamadı")

        # PDF oluştur (Bloklayıcı işlemi thread'e taşı)
        generator = get_report_generator()
        pdf_bytes = await asyncio.to_thread(
            generator.generate_vehicle_report, arac_id, month, year, data
        )

        plaka = data.get("plaka", f"arac_{arac_id}")
        # Sanitize filename (Header Injection Protection)
        safe_plaka = "".join(c for c in plaka if c.isalnum() or c in ("-", "_")).strip()
        filename = f"{safe_plaka}_{month:02d}_{year}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pdf/driver-comparison")
async def get_driver_comparison_pdf(
    db: SessionDep, current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Şoför performans karşılaştırma raporu PDF
    """
    try:
        from app.core.services.sofor_analiz_service import get_sofor_analiz_service

        sofor_service = get_sofor_analiz_service()
        drivers = await sofor_service.get_driver_stats()

        # Driver dict listesine dönüştür
        driver_data = [
            {
                "ad_soyad": d.ad_soyad,
                "trips": d.toplam_sefer,
                "consumption": d.ort_tuketim,
                "score": d.performans_puani,
            }
            for d in drivers
        ]

        generator = get_report_generator()
        pdf_bytes = await asyncio.to_thread(
            generator.generate_driver_comparison, driver_data
        )

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=sofor_karsilastirma_{date.today()}.pdf"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost/period", response_model=CostBreakdownResponse)
async def get_period_cost(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    start_date: str = Query(...),
    end_date: str = Query(...),
    arac_id: Optional[int] = Query(None),
):
    """
    Dönemsel maliyet analizi
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Geçersiz tarih formatı. YYYY-MM-DD kullanın."
        )

    analyzer = get_cost_analyzer()
    breakdown = await analyzer.calculate_period_cost(start, end, arac_id)

    return CostBreakdownResponse(
        fuel_cost=float(breakdown.fuel_cost),
        fuel_liters=breakdown.fuel_liters,
        avg_price_per_liter=float(breakdown.avg_price_per_liter),
        trip_count=breakdown.trip_count,
        total_distance=breakdown.total_distance,
        cost_per_km=float(breakdown.cost_per_km),
        period_start=breakdown.period_start.isoformat(),
        period_end=breakdown.period_end.isoformat(),
    )


@router.get("/cost/trend")
async def get_cost_trend(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    months: int = Query(12, ge=1, le=24),
):
    """
    Aylık maliyet trendi
    """
    analyzer = get_cost_analyzer()
    return await analyzer.get_monthly_trend(months)


@router.get("/cost/vehicle-comparison")
async def get_vehicle_cost_comparison(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    months: int = Query(3, ge=1, le=12),
):
    """
    Araç bazlı maliyet karşılaştırması
    """
    analyzer = get_cost_analyzer()
    return await analyzer.get_vehicle_cost_comparison(months)


@router.get("/cost/savings-potential", response_model=SavingsPotentialResponse)
async def get_savings_potential(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    target_consumption: float = Query(30.0, ge=20, le=45),
):
    """
    Tasarruf potansiyeli hesaplama
    """
    analyzer = get_cost_analyzer()
    result = await analyzer.calculate_savings_potential(target_consumption)

    return SavingsPotentialResponse(**result)


@router.get("/cost/roi", response_model=ROIResponse)
async def get_roi_analysis(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    investment: float = Query(50000, ge=0),
    months: int = Query(12, ge=3, le=24),
):
    """
    Sistem ROI analizi
    """
    analyzer = get_cost_analyzer()
    result = analyzer.calculate_roi(investment, months)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return ROIResponse(**result)


@router.get("/excel/template/{entity_type}")
async def get_excel_template(
    entity_type: str,
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
):
    """
    Excel yükleme şablonu indir

    Args:
        entity_type: yakit, sefer, arac, sofor
    """
    export_service = get_export_service()
    filepath = await asyncio.to_thread(export_service.generate_template, entity_type)

    if not filepath:
        raise HTTPException(status_code=404, detail="Şablon oluşturulamadı")

    import os

    filename = os.path.basename(filepath)

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
