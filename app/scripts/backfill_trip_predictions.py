import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional

from sqlalchemy import func, select

sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.models import Sefer
from app.services.prediction_service import get_prediction_service


DEFAULT_STATE_PATH = Path("data/backfill_trip_predictions.state.json")


def _load_state(state_path: Path) -> Dict[str, Any]:
    if not state_path.exists():
        return {"last_id": 0}
    try:
        with state_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_id": 0}


def _save_state(state_path: Path, state: Dict[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _extract_prediction_payload(
    prediction: Optional[Dict[str, Any]],
    quality_flags: Dict[str, Any],
) -> tuple[Optional[float], Optional[Dict[str, Any]]]:
    if not prediction:
        return None, None

    tahmini_tuketim = prediction.get("tahmini_tuketim")
    if tahmini_tuketim is None:
        return None, None

    try:
        tahmini_tuketim = float(tahmini_tuketim)
    except (TypeError, ValueError):
        return None, None

    meta = {
        "model_used": prediction.get("model_used"),
        "model_version": prediction.get("model_version"),
        "confidence_score": prediction.get("confidence_score"),
        "confidence_low": prediction.get("confidence_low"),
        "confidence_high": prediction.get("confidence_high"),
        "warning_level": prediction.get("warning_level"),
        "fallback_triggered": bool(prediction.get("fallback_triggered", False)),
        "faktorler": prediction.get("faktorler") or {},
        "explanation_summary": prediction.get("explanation_summary"),
        "input_quality": quality_flags,
    }
    return tahmini_tuketim, meta


async def _backfill(args: argparse.Namespace) -> None:
    state_path = Path(args.state_file)
    state = _load_state(state_path) if args.resume else {"last_id": 0}
    last_id = max(int(args.start_after_id or 0), int(state.get("last_id", 0)))

    prediction_service = get_prediction_service()
    processed = 0
    updated = 0

    async with AsyncSessionLocal() as session:
        target_total_query = select(func.count()).select_from(Sefer).where(
            Sefer.is_deleted.is_(False),
            Sefer.mesafe_km > 0,
        )
        target_total = int((await session.execute(target_total_query)).scalar() or 0)
        print(f"[backfill] target_total={target_total}, start_after_id={last_id}")

        while True:
            stmt = (
                select(Sefer)
                .where(
                    Sefer.is_deleted.is_(False),
                    Sefer.mesafe_km > 0,
                    Sefer.id > last_id,
                )
                .order_by(Sefer.id.asc())
                .limit(args.chunk_size)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
            if not rows:
                break

            for trip in rows:
                quality_flags = {
                    "route_available": bool(trip.guzergah_id or trip.rota_detay),
                    "ascent_available": trip.ascent_m is not None,
                    "descent_available": trip.descent_m is not None,
                    "flat_distance_available": trip.flat_distance_km is not None,
                    "degrade_mode": not bool(trip.guzergah_id or trip.rota_detay),
                    "weather_available": False,
                }

                try:
                    route_analysis_payload: Dict[str, Any] = {}
                    if isinstance(trip.rota_detay, dict):
                        route_analysis_payload.update(trip.rota_detay)
                    if "ratios" not in route_analysis_payload:
                        total_km = float(trip.mesafe_km or 0.0)
                        oto_km = float(trip.otoban_mesafe_km or 0.0)
                        sehir_km = float(trip.sehir_ici_mesafe_km or 0.0)
                        if total_km > 0:
                            oto_ratio = max(0.0, min(1.0, oto_km / total_km))
                            sehir_ratio = max(0.0, min(1.0, sehir_km / total_km))
                            route_analysis_payload["ratios"] = {
                                "otoyol": round(oto_ratio, 3),
                                "devlet_yolu": round(
                                    max(0.0, 1.0 - oto_ratio - sehir_ratio), 3
                                ),
                                "sehir_ici": round(sehir_ratio, 3),
                            }

                    prediction = await prediction_service.predict_consumption(
                        arac_id=trip.arac_id,
                        mesafe_km=float(trip.mesafe_km or 0.0),
                        ton=float(trip.ton or 0.0),
                        ascent_m=float(trip.ascent_m or 0.0),
                        descent_m=float(trip.descent_m or 0.0),
                        flat_distance_km=float(trip.flat_distance_km or 0.0),
                        sofor_id=trip.sofor_id,
                        dorse_id=trip.dorse_id,
                        target_date=trip.tarih,
                        bos_sefer=bool(trip.bos_sefer),
                        route_analysis=route_analysis_payload or None,
                    )
                except Exception as exc:
                    print(f"[warn] prediction failed for trip#{trip.id}: {exc}")
                    last_id = trip.id
                    processed += 1
                    continue

                weather_available = bool(
                    prediction.get("faktorler", {}).get("weather_factor")
                )
                quality_flags["weather_available"] = weather_available
                quality_flags["degrade_mode"] = bool(
                    quality_flags["degrade_mode"] or not weather_available
                )

                tahmini_tuketim, tahmin_meta = _extract_prediction_payload(
                    prediction, quality_flags=quality_flags
                )
                if tahmini_tuketim is not None and tahmin_meta is not None:
                    trip.tahmini_tuketim = tahmini_tuketim
                    trip.tahmin_meta = tahmin_meta
                    updated += 1

                last_id = trip.id
                processed += 1

                if args.max_trips and processed >= args.max_trips:
                    break

            if args.dry_run:
                await session.rollback()
            else:
                await session.commit()
                _save_state(state_path, {"last_id": last_id, "processed": processed})

            print(
                f"[backfill] processed={processed}, updated={updated}, last_id={last_id}"
            )

            if args.max_trips and processed >= args.max_trips:
                break

        covered_query = select(func.count()).select_from(Sefer).where(
            Sefer.is_deleted.is_(False),
            Sefer.mesafe_km > 0,
            Sefer.tahmini_tuketim.is_not(None),
            Sefer.tahmin_meta.is_not(None),
        )
        covered = int((await session.execute(covered_query)).scalar() or 0)
        coverage_pct = (covered / target_total * 100.0) if target_total else 0.0
        print(
            f"[backfill] coverage={covered}/{target_total} ({coverage_pct:.2f}%), dry_run={args.dry_run}"
        )

        mae_query = select(func.avg(func.abs(Sefer.tuketim - Sefer.tahmini_tuketim))).where(
            Sefer.is_deleted.is_(False),
            Sefer.tuketim.is_not(None),
            Sefer.tuketim > 0,
            Sefer.tahmini_tuketim.is_not(None),
        )
        current_mae = float((await session.execute(mae_query)).scalar() or 0.0)
        print(f"[backfill] current_mae={current_mae:.4f}")

        if args.require_full_coverage and coverage_pct < 100.0:
            raise SystemExit(
                f"Coverage gate failed: {coverage_pct:.2f}% (required: 100.00%)"
            )

        if args.baseline_mae > 0:
            improvement_pct = ((args.baseline_mae - current_mae) / args.baseline_mae) * 100
            print(
                f"[backfill] mae_improvement={improvement_pct:.2f}% "
                f"(required: {args.required_improvement_pct:.2f}%)"
            )
            if improvement_pct < args.required_improvement_pct:
                raise SystemExit(
                    "MAE gate failed: "
                    f"{improvement_pct:.2f}% < {args.required_improvement_pct:.2f}%"
                )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Backfill tahmini_tuketim + tahmin_meta for trips."
    )
    parser.add_argument("--chunk-size", type=int, default=200)
    parser.add_argument("--start-after-id", type=int, default=0)
    parser.add_argument("--max-trips", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--require-full-coverage", action="store_true")
    parser.add_argument("--baseline-mae", type=float, default=0.0)
    parser.add_argument("--required-improvement-pct", type=float, default=15.0)
    parser.add_argument("--state-file", type=str, default=str(DEFAULT_STATE_PATH))
    return parser


async def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    await _backfill(args)


if __name__ == "__main__":
    asyncio.run(main())
