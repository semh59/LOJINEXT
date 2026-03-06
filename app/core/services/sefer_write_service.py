"""
TIR Yakıt Takip Sistemi - Sefer Yazma Servisi
Command-Query Separation (CQS) prensibi gereği yazma (Create/Update/Delete) işlemlerini yönetir.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import traceback

from app.core.entities.models import SeferCreate, SeferUpdate
from app.database.unit_of_work import UnitOfWork
from app.infrastructure.audit import audit_log
from app.infrastructure.events.event_bus import (
    EventBus,
    EventType,
    get_event_bus,
    publishes,
)
from app.database.repositories.sefer_repo import SeferRepository, get_sefer_repo
from app.infrastructure.logging.logger import get_logger
from app.core.services.route_validator import RouteValidator

logger = get_logger(__name__)


class SeferWriteService:
    """
    Sefer yazma işlemleri (Create, Update, Delete).
    """

    def __init__(
        self,
        repo: Optional[SeferRepository] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.repo = repo or get_sefer_repo()
        self.event_bus = event_bus or get_event_bus()

    async def _refresh_stats(self, uow: UnitOfWork) -> None:
        """İstatistik MV'sini arka planda yenileyen tetikleyici (Daha güvenli)."""
        try:
            # We use the repository from the active UoW to refresh
            await uow.sefer_repo.refresh_stats_mv()
        except Exception as e:
            logger.error(f"Post-write stats refresh failed: {e}")

    async def _create_return_trip(
        self,
        uow: Any,
        data: SeferCreate,
        trip_date: date,
        ref_sefer_id: int,
        weather_factor: float = 1.0,
        route_details: Optional[Dict] = None,
        user_id: Optional[int] = None,
    ) -> None:
        """Helper to create return trip logic (Atomicity support)"""
        return_kg = data.return_net_kg or 0

        is_empty = return_kg == 0

        # Guard: Ensure return_sefer_no has suffix and swap logic is sound
        base_sn = data.sefer_no
        return_sn = data.return_sefer_no
        if not return_sn and base_sn:
            if not base_sn.endswith("-D"):
                return_sn = f"{base_sn}-D"
            else:
                return_sn = f"{base_sn}-R"  # Rare case: return of a return?

        return_tahmini = None
        if data.arac_id and data.mesafe_km:
            try:
                from app.services.prediction_service import get_prediction_service

                pred_service = get_prediction_service()

                logger.info(
                    f"Predicting Return Trip: {data.varis_yeri} -> {data.cikis_yeri}, {return_kg}kg"
                )

                return_prediction = await pred_service.predict_consumption(
                    arac_id=data.arac_id,
                    mesafe_km=data.mesafe_km,
                    ton=round(return_kg / 1000, 2),
                    ascent_m=data.descent_m or 0.0,
                    descent_m=data.ascent_m or 0.0,
                    flat_distance_km=data.flat_distance_km or 0.0,
                    sofor_id=data.sofor_id,
                    target_date=trip_date,
                    bos_sefer=is_empty,
                    route_analysis={"weather_factor": weather_factor},
                )
                if return_prediction and "prediction_liters" in return_prediction:
                    return_tahmini = float(return_prediction["prediction_liters"])
            except Exception as rpe:
                logger.warning(f"Return prediction failed: {rpe}")

        await uow.sefer_repo.add(
            tarih=trip_date,
            arac_id=data.arac_id,
            sofor_id=data.sofor_id,
            guzergah_id=data.guzergah_id,
            mesafe_km=data.mesafe_km,
            net_kg=return_kg,
            sefer_no=return_sn,
            bos_agirlik_kg=data.bos_agirlik_kg,
            dolu_agirlik_kg=0,
            cikis_yeri=data.varis_yeri,
            varis_yeri=data.cikis_yeri,
            saat=data.saat or "",
            bos_sefer=is_empty,
            durum=data.durum or "Bekliyor",
            ascent_m=data.descent_m or 0.0,
            descent_m=data.ascent_m or 0.0,
            flat_distance_km=data.flat_distance_km or 0.0,
            tahmini_tuketim=return_tahmini,
            rota_detay=route_details.get("route_analysis") if route_details else None,
            otoban_mesafe_km=route_details.get("otoban_mesafe_km")
            if route_details
            else None,
            sehir_ici_mesafe_km=route_details.get("sehir_ici_mesafe_km")
            if route_details
            else None,
            notlar=f"Dönüş seferi (Ref: #{ref_sefer_id})",
            is_real=data.is_real,
            created_by_id=user_id,
        )

    @audit_log("CREATE", "sefer")
    @publishes(EventType.SEFER_ADDED)
    async def add_sefer(self, data: SeferCreate, user_id: Optional[int] = None) -> int:
        """
        Yeni sefer ekle. (Round-trip & Backhaul desteği ile)
        """
        try:
            async with UnitOfWork() as uow:
                # 1. Validation Logic
                if data.cikis_yeri == data.varis_yeri:
                    raise ValueError("Çıkış ve varış yeri aynı olamaz")

                # Normalize names
                data.cikis_yeri = data.cikis_yeri.strip().title()
                data.varis_yeri = data.varis_yeri.strip().title()

                if data.mesafe_km <= 0:
                    raise ValueError("Mesafe 0'dan büyük olmalıdır")

                # Parse date
                trip_date = (
                    data.tarih
                    if isinstance(data.tarih, date)
                    else date.fromisoformat(str(data.tarih))
                )

                # Future date check (Elite Guard)
                if trip_date > date.today() + timedelta(days=365):
                    raise ValueError(
                        "Sefer tarihi 1 yıldan daha ileri bir tarih olamaz"
                    )

                # Sefer No duplicate check
                if data.sefer_no:
                    existing_sn = await uow.sefer_repo.get_by_sefer_no(data.sefer_no)
                    if existing_sn:
                        raise ValueError(
                            f"Bu sefer numarası zaten kullanımda: {data.sefer_no}"
                        )

                # Active Trip Check (Elite Guard)
                # Yeni sefer "Devam Ediyor" veya "Yolda" olarak açılıyorsa kontrol et
                if data.durum in ("Devam Ediyor", "Yolda"):
                    has_active = await uow.sefer_repo.has_active_trip(data.arac_id)
                    if has_active:
                        raise ValueError(
                            f"Araç (ID: {data.arac_id}) zaten aktif bir seferde. Yeni aktif sefer açılamaz."
                        )

                # 2. Database Checks
                arac = await uow.arac_repo.get_by_id(data.arac_id)
                if not arac or not arac.get("aktif"):
                    raise ValueError("Seçilen araç bulunamadı veya pasif.")

                sofor = await uow.sofor_repo.get_by_id(data.sofor_id)
                if not sofor or not sofor.get("aktif"):
                    raise ValueError("Seçilen şoför bulunamadı veya pasif.")

                # Güzergah metadata kalıtımı (Eğer guzergah_id varsa)
                route_dict = None
                if data.guzergah_id:
                    route_dict = await uow.lokasyon_repo.get_by_id(data.guzergah_id)
                    if route_dict:
                        if not data.mesafe_km:
                            data.mesafe_km = route_dict.get("mesafe_km", 0.0)
                        if not data.ascent_m:
                            data.ascent_m = route_dict.get("ascent_m", 0.0)
                        if not data.descent_m:
                            data.descent_m = route_dict.get("descent_m", 0.0)

                # Validate and correct route data (Elevation anomalies check)
                temp_dict = data.model_dump()
                corrected = RouteValidator.validate_and_correct(temp_dict)
                if corrected.get("is_corrected"):
                    data.ascent_m = corrected["ascent_m"]
                    data.descent_m = corrected["descent_m"]
                    logger.info(
                        f"API Add: Corrected anomalous elevation to {data.ascent_m}m"
                    )

                # 3. YAKIT TAHMİNİ (Gidiş Leg)
                tahmini_tuk = None
                weather_factor = 1.0

                if data.arac_id and data.mesafe_km:
                    try:
                        from app.services.prediction_service import (
                            get_prediction_service,
                        )
                        from app.core.services.weather_service import (
                            get_weather_service,
                        )

                        pred_service = get_prediction_service()
                        weather_service = get_weather_service()

                        if data.guzergah_id and route_dict:
                            try:
                                c_lat = route_dict.get("cikis_lat")
                                c_lon = route_dict.get("cikis_lon")
                                v_lat = route_dict.get("varis_lat")
                                v_lon = route_dict.get("varis_lon")
                                if c_lat and v_lat:
                                    w_res = (
                                        await weather_service.get_trip_impact_analysis(
                                            cikis_lat=c_lat,
                                            cikis_lon=c_lon,
                                            varis_lat=v_lat,
                                            varis_lon=v_lon,
                                        )
                                    )
                                    if w_res.get("success"):
                                        weather_factor = w_res.get(
                                            "fuel_impact_factor", 1.0
                                        )
                            except Exception as we:
                                logger.warning(f"Weather failed: {we}")

                        prediction = await pred_service.predict_consumption(
                            arac_id=data.arac_id,
                            mesafe_km=data.mesafe_km,
                            ton=data.ton or round(data.net_kg / 1000, 2),
                            ascent_m=data.ascent_m or 0.0,
                            descent_m=data.descent_m or 0.0,
                            flat_distance_km=data.flat_distance_km or 0.0,
                            sofor_id=data.sofor_id,
                            target_date=trip_date,
                            bos_sefer=data.bos_sefer,
                            dorse_id=data.dorse_id,
                            route_analysis={"weather_factor": weather_factor},
                        )

                        if prediction and "prediction_liters" in prediction:
                            tahmini_tuk = float(prediction["prediction_liters"])
                    except Exception as pe:
                        logger.error(f"Tahmin servisi hatası: {pe}")

                # Ağırlık senkronizasyonu
                b_kg = data.bos_agirlik_kg or arac.get("bos_agirlik_kg", 0)
                n_kg = data.net_kg or 0
                d_kg = data.dolu_agirlik_kg or (b_kg + n_kg)

                # Eğer dolu ağırlık belirtilmişse net ağırlığı yeniden hesapla
                if data.dolu_agirlik_kg:
                    n_kg = d_kg - b_kg
                else:
                    d_kg = b_kg + n_kg

                # Model verilerini güncelle
                data.bos_agirlik_kg = b_kg
                data.dolu_agirlik_kg = d_kg
                data.net_kg = n_kg
                data.ton = round(n_kg / 1000.0, 2)

                # 4. DB Insert (Gidiş)
                sefer_id = await uow.sefer_repo.add(
                    tarih=trip_date,
                    arac_id=data.arac_id,
                    sofor_id=data.sofor_id,
                    dorse_id=data.dorse_id,
                    guzergah_id=data.guzergah_id,
                    mesafe_km=data.mesafe_km,
                    net_kg=data.net_kg,
                    sefer_no=data.sefer_no,
                    bos_agirlik_kg=data.bos_agirlik_kg,
                    dolu_agirlik_kg=data.dolu_agirlik_kg,
                    cikis_yeri=data.cikis_yeri,
                    varis_yeri=data.varis_yeri,
                    saat=data.saat or "",
                    bos_sefer=data.bos_sefer,
                    durum=data.durum or "Bekliyor",
                    ascent_m=data.ascent_m or 0.0,
                    descent_m=data.descent_m or 0.0,
                    flat_distance_km=data.flat_distance_km or 0.0,
                    tahmini_tuketim=tahmini_tuk,
                    rota_detay=route_dict.get("route_analysis") if route_dict else None,
                    otoban_mesafe_km=route_dict.get("otoban_mesafe_km")
                    if route_dict
                    else None,
                    sehir_ici_mesafe_km=route_dict.get("sehir_ici_mesafe_km")
                    if route_dict
                    else None,
                    notlar=data.notlar,
                    created_by_id=user_id,
                )

                # 5. ROUND-TRIP (Dönüş Seferi)
                logger.info(
                    f"Checking Round Trip: {data.is_round_trip}, ReturnKg: {data.return_net_kg}"
                )
                if data.is_round_trip:
                    await self._create_return_trip(
                        uow,
                        data,
                        trip_date,
                        sefer_id,
                        weather_factor,
                        route_details=route_dict,
                        user_id=user_id,
                    )

                # 6. Atomic Commit
                await uow.commit()
                # 7. Refresh Stats (Post-commit)
                await self._refresh_stats(uow)
                logger.info(f"Sefer(ler) başarıyla kaydedildi. ID: {sefer_id}")
                return int(sefer_id)

        except Exception as e:
            logger.error(f"Sefer ekleme hatası: {e}\n{traceback.format_exc()}")
            raise

    @audit_log("UPDATE", "sefer")
    @publishes(EventType.SEFER_UPDATED)
    async def update_sefer(
        self, sefer_id: int, data: SeferUpdate, user_id: Optional[int] = None
    ) -> bool:
        """Sefer güncelle (Atomik)."""
        async with UnitOfWork() as uow:
            success = await self._update_sefer_uow(uow, sefer_id, data, user_id)
            if success:
                await uow.commit()
                await self._refresh_stats(uow)
            return success

    async def _update_sefer_uow(
        self,
        uow: UnitOfWork,
        sefer_id: int,
        data: SeferUpdate,
        user_id: Optional[int] = None,
    ) -> bool:
        """Sefer güncelleme mantığı (Paylaşımlı UoW destekli)."""
        # Status Transition Matrix (Elite Guard)
        # Defines which statuses can move to which
        VALID_TRANSITIONS = {
            "Bekliyor": ["Yolda", "Devam Ediyor", "İptal", "Planlandı"],
            "Planlandı": ["Yolda", "Devam Ediyor", "İptal", "Bekliyor"],
            "Yolda": ["Tamamlandı", "Tamam", "İptal"],
            "Devam Ediyor": ["Tamamlandı", "Tamam", "İptal"],
            "Tamamlandı": [],
            "Tamam": [],
            "İptal": [],
        }

        try:
            # Fetch current state for transition check
            current_sefer = await uow.sefer_repo.get_by_id(sefer_id, for_update=True)
            if not current_sefer:
                raise ValueError(f"Sefer bulunamadı: {sefer_id}")

            # model_dump(exclude_unset=True) ensures we only update fields provided in the request
            update_data = data.model_dump(exclude_unset=True)
            if not update_data:
                return True  # Nothing to update

            # Status Transition Validation
            new_status = update_data.get("durum")
            if new_status:
                old_status = current_sefer.get("durum", "Bekliyor")
                if old_status != new_status:
                    allowed = VALID_TRANSITIONS.get(old_status, [])
                    if new_status not in allowed:
                        raise ValueError(
                            f"Geçersiz durum geçişi: '{old_status}' -> '{new_status}'"
                        )

            if user_id is not None:
                update_data["updated_by_id"] = user_id

            # Sefer No duplicate check for update
            if "sefer_no" in update_data and update_data["sefer_no"]:
                if current_sefer.get("sefer_no") != update_data["sefer_no"]:
                    existing = await uow.sefer_repo.get_by_sefer_no(
                        update_data["sefer_no"]
                    )
                    if existing:
                        raise ValueError(
                            f"Bu sefer numarası zaten kullanımda: {update_data['sefer_no']}"
                        )

            # Active Trip Check for Update
            target_arac_id = update_data.get("arac_id")

            # Eğer durum 'Yolda'/'Devam Ediyor' olarak değişiyorsa veya araç değişip aktif kalıyorsa
            if new_status in ("Devam Ediyor", "Yolda"):
                # Aracı veritabanından al (Eğer update_data'da yoksa)
                if not target_arac_id:
                    target_arac_id = current_sefer.get("arac_id")

                if target_arac_id:
                    has_active = await uow.sefer_repo.has_active_trip(
                        target_arac_id, exclude_sefer_id=sefer_id
                    )
                    if has_active:
                        raise ValueError(
                            f"Araç zaten başka bir aktif seferde. Bu seferin durumu '{new_status}' yapılamaz."
                        )

            # RE-PREDICTION LOGIC
            # Check if fields affecting fuel prediction are changed
            repredict_fields = {
                "guzergah_id",
                "arac_id",
                "sofor_id",
                "net_kg",
                "ton",
                "tarih",
                "bos_sefer",
                "dorse_id",
            }
            if any(field in update_data for field in repredict_fields):
                # Build prediction parameters (merging old and new data)
                pred_arac_id = update_data.get("arac_id", current_sefer.get("arac_id"))
                pred_sofor_id = update_data.get(
                    "sofor_id", current_sefer.get("sofor_id")
                )
                pred_tarih = update_data.get("tarih", current_sefer.get("tarih"))
                pred_bos_sefer = update_data.get(
                    "bos_sefer", current_sefer.get("bos_sefer")
                )
                pred_dorse_id = update_data.get(
                    "dorse_id", current_sefer.get("dorse_id")
                )

                # Tonaj logic (Standardized)
                pred_ton = update_data.get("ton")
                if pred_ton is None:
                    pred_net_kg = update_data.get(
                        "net_kg", current_sefer.get("net_kg", 0)
                    )
                    pred_ton = float(pred_net_kg) / 1000.0 if pred_net_kg else 0.0

                # If it's an empty return (bos_sefer), ton is essentially 0
                if pred_bos_sefer:
                    pred_ton = 0.0

                # Get route info if available
                pred_mesafe = update_data.get(
                    "mesafe_km", current_sefer.get("mesafe_km", 0.0)
                )
                pred_ascent = update_data.get(
                    "ascent_m", current_sefer.get("ascent_m", 0.0)
                )
                pred_descent = update_data.get(
                    "descent_m", current_sefer.get("descent_m", 0.0)
                )
                pred_flat = update_data.get(
                    "flat_distance_km", current_sefer.get("flat_distance_km", 0.0)
                )

                # Enrich from NEW route if changed
                if "guzergah_id" in update_data and update_data["guzergah_id"]:
                    route_dict = await uow.lokasyon_repo.get_by_id(
                        update_data["guzergah_id"]
                    )
                    if route_dict:
                        pred_mesafe = route_dict.get("mesafe_km", pred_mesafe)
                        pred_ascent = route_dict.get("ascent_m", pred_ascent)
                        pred_descent = route_dict.get("descent_m", pred_descent)
                        pred_flat = route_dict.get("flat_distance_km", pred_flat)
                        # Actually apply these to update_data as well
                        update_data["mesafe_km"] = pred_mesafe
                        update_data["ascent_m"] = pred_ascent
                        update_data["descent_m"] = pred_descent
                        update_data["flat_distance_km"] = pred_flat

                        # Enhanced Route Data
                        if "route_analysis" in route_dict:
                            update_data["rota_detay"] = route_dict["route_analysis"]
                        if "otoban_mesafe_km" in route_dict:
                            update_data["otoban_mesafe_km"] = route_dict[
                                "otoban_mesafe_km"
                            ]
                        if "sehir_ici_mesafe_km" in route_dict:
                            update_data["sehir_ici_mesafe_km"] = route_dict[
                                "sehir_ici_mesafe_km"
                            ]

                # Trigger Prediction
                try:
                    logger.info(
                        f"Triggering PREDICTION: Arac={pred_arac_id}, Mesafe={pred_mesafe}, Ton={pred_ton}, Empty={pred_bos_sefer}"
                    )
                    from app.services.prediction_service import (
                        get_prediction_service,
                    )

                    pred_service = get_prediction_service()

                    prediction = await pred_service.predict_consumption(
                        arac_id=pred_arac_id,
                        mesafe_km=pred_mesafe,
                        ton=pred_ton,
                        ascent_m=pred_ascent,
                        descent_m=pred_descent,
                        flat_distance_km=pred_flat,
                        sofor_id=pred_sofor_id,
                        target_date=pred_tarih
                        if isinstance(pred_tarih, date)
                        else date.fromisoformat(str(pred_tarih)),
                        bos_sefer=pred_bos_sefer,
                        dorse_id=pred_dorse_id,
                    )
                    if prediction and "prediction_liters" in prediction:
                        update_data["tahmini_tuketim"] = float(
                            prediction["prediction_liters"]
                        )
                        logger.info(
                            f"Re-prediction SUCCESS: {update_data['tahmini_tuketim']} L"
                        )
                except Exception as pe:
                    logger.error(f"Re-prediction error: {pe}", exc_info=True)

            # Validate and correct route data before final database write
            update_data = RouteValidator.validate_and_correct(update_data)

            # Ağırlık senkronizasyonu (Elite Guard)
            # dolu - bos = net kısıtının bozulmaması için tüm alanlar güncellenir.
            if any(
                k in update_data
                for k in ["net_kg", "bos_agirlik_kg", "dolu_agirlik_kg"]
            ):
                # Değerleri al (yeni yoksa mevcut olanı kullan)
                b_kg = update_data.get(
                    "bos_agirlik_kg", current_sefer.get("bos_agirlik_kg", 0)
                )
                d_kg = update_data.get(
                    "dolu_agirlik_kg", current_sefer.get("dolu_agirlik_kg", 0)
                )
                n_kg = update_data.get("net_kg", current_sefer.get("net_kg", 0))

                # Öncelik sırasına göre hesapla
                if "dolu_agirlik_kg" in update_data or "bos_agirlik_kg" in update_data:
                    # Dolu veya Boş değiştiyse Net'i güncelle
                    n_kg = d_kg - b_kg
                    update_data["net_kg"] = n_kg
                elif "net_kg" in update_data:
                    # Sadece Net değiştiyse Dolu'yu güncelle
                    d_kg = b_kg + n_kg
                    update_data["dolu_agirlik_kg"] = d_kg

                # Tonajı her durumda güncelle
                update_data["ton"] = round(n_kg / 1000.0, 2)

            success = await uow.sefer_repo.update_sefer(id=sefer_id, **update_data)

            if success:
                # ROUTE EVENTS (Elite Global Rule)
                if new_status:
                    if new_status in ("Yolda", "Devam Ediyor"):
                        await self.event_bus.publish(
                            EventType.ROUTE_STARTED,
                            {
                                "sefer_id": sefer_id,
                                "arac_id": target_arac_id
                                or current_sefer.get("arac_id"),
                            },
                        )
                    elif new_status in ("Tamamlandı", "Tamam"):
                        await self.event_bus.publish(
                            EventType.ROUTE_COMPLETED,
                            {
                                "sefer_id": sefer_id,
                                "arac_id": target_arac_id
                                or current_sefer.get("arac_id"),
                            },
                        )

                        # SLA CHECK: Gecikme Kontrolü
                        try:
                            # Use full data from current_sefer and update_data
                            # actual_duration is in current_sefer or might be updated
                            current_full = await uow.sefer_repo.get_by_id(sefer_id)
                            if current_full:
                                actual_duration = current_full.get("duration_min")
                                planned_duration_min = 0
                                if current_full.get("guzergah_id"):
                                    route = await uow.lokasyon_repo.get_by_id(
                                        current_full["guzergah_id"]
                                    )
                                    if route and route.get("tahmini_sure_saat"):
                                        planned_duration_min = int(
                                            route["tahmini_sure_saat"] * 60
                                        )

                                if planned_duration_min > 0 and actual_duration:
                                    if actual_duration > (planned_duration_min * 1.2):
                                        delay_min = (
                                            actual_duration - planned_duration_min
                                        )
                                        await self.event_bus.publish(
                                            EventType.SLA_DELAY,
                                            {
                                                "sefer_id": sefer_id,
                                                "arac_id": target_arac_id
                                                or current_sefer.get("arac_id"),
                                                "planned_min": planned_duration_min,
                                                "actual_min": actual_duration,
                                                "delay_min": delay_min,
                                            },
                                        )

                        except Exception as sla_err:
                            logger.error(f"SLA Check fail: {sla_err}")

                # ROUND-TRIP CHECK
                if update_data.get("is_round_trip"):
                    try:
                        current_full = await uow.sefer_repo.get_by_id(sefer_id)
                        if current_full:
                            from app.core.entities.models import SeferCreate

                            create_data_dict = {
                                "sefer_no": current_full.get("sefer_no"),
                                "tarih": current_full.get("tarih"),
                                "saat": current_full.get("saat"),
                                "arac_id": current_full.get("arac_id"),
                                "sofor_id": current_full.get("sofor_id"),
                                "guzergah_id": current_full.get("guzergah_id"),
                                "cikis_yeri": current_full.get("cikis_yeri"),
                                "varis_yeri": current_full.get("varis_yeri"),
                                "mesafe_km": current_full.get("mesafe_km"),
                                "bos_agirlik_kg": current_full.get("bos_agirlik_kg"),
                                "dolu_agirlik_kg": current_full.get("dolu_agirlik_kg"),
                                "net_kg": current_full.get("net_kg"),
                                "bos_sefer": current_full.get("bos_sefer"),
                                "durum": current_full.get("durum"),
                                "is_round_trip": True,
                                "return_net_kg": update_data.get("return_net_kg", 0),
                                "return_sefer_no": update_data.get("return_sefer_no"),
                                "ascent_m": current_full.get("ascent_m"),
                                "descent_m": current_full.get("descent_m"),
                                "flat_distance_km": current_full.get(
                                    "flat_distance_km"
                                ),
                            }
                            full_sefer_obj = SeferCreate(**create_data_dict)
                            potential_return_no = f"{full_sefer_obj.sefer_no}-D"
                            existing_return = await uow.sefer_repo.get_by_sefer_no(
                                potential_return_no
                            )

                            if not existing_return:
                                await self._create_return_trip(
                                    uow, full_sefer_obj, full_sefer_obj.tarih, sefer_id
                                )
                    except Exception as re:
                        logger.error(f"Failed to create return trip: {re}")

            return bool(success)

        except Exception as e:
            logger.error(f"Sefer guncelleme hatasi (UoW): {e}")
            raise

    @audit_log("DELETE", "sefer")
    @publishes(EventType.SEFER_DELETED)
    async def delete_sefer(self, sefer_id: int) -> bool:
        """Sefer sil (Soft Delete - Atomik)."""
        async with UnitOfWork() as uow:
            success = await self._delete_sefer_uow(uow, sefer_id)
            if success:
                await uow.commit()
                await self._refresh_stats(uow)
            return success

    async def _delete_sefer_uow(self, uow: UnitOfWork, sefer_id: int) -> bool:
        """Sefer silme mantığı (Paylaşımlı UoW destekli)."""
        try:
            # Soft delete by default, as per audit result
            success = await uow.sefer_repo.delete(sefer_id)
            if success:
                logger.info(f"Sefer silindi (Soft Deleted): ID {sefer_id}")
            return bool(success)
        except Exception as e:
            logger.error(f"Sefer silme hatasi (UoW): {e}")
            raise

    async def bulk_update_status(
        self, sefer_ids: List[int], new_status: str, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Birden fazla seferin durumunu toplu güncelle.
        N+1 Transaction sorunu giderildi (Tek UoW).
        """
        success_count = 0
        failed = []

        from app.core.entities.models import SeferUpdate

        async with UnitOfWork() as uow:
            for sid in sefer_ids:
                try:
                    success = await self._update_sefer_uow(
                        uow, sid, SeferUpdate(durum=new_status), user_id=user_id
                    )
                    if success:
                        success_count += 1
                    else:
                        failed.append(
                            {"id": sid, "reason": "Bulunamadı veya güncellenemedi"}
                        )
                except Exception as e:
                    logger.error(f"Bulk status update error for sid {sid}: {e}")
                    failed.append({"id": sid, "reason": str(e)})

            if success_count > 0:
                await uow.commit()
                await self._refresh_stats(uow)

        return {
            "success_count": success_count,
            "failed_count": len(failed),
            "failed": failed,
        }

    async def bulk_cancel(
        self,
        sefer_ids: List[int],
        iptal_nedeni: str,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Birden fazla seferi toplu iptal et.
        N+1 Transaction sorunu giderildi.
        """
        success_count = 0
        failed = []

        from app.core.entities.models import SeferUpdate

        async with UnitOfWork() as uow:
            for sid in sefer_ids:
                try:
                    success = await self._update_sefer_uow(
                        uow,
                        sid,
                        SeferUpdate(durum="İptal", iptal_nedeni=iptal_nedeni),
                        user_id=user_id,
                    )
                    if success:
                        success_count += 1
                    else:
                        failed.append(
                            {"id": sid, "reason": "Bulunamadı veya iptal edilemedi"}
                        )
                except Exception as e:
                    logger.error(f"Bulk cancel error for sid {sid}: {e}")
                    failed.append({"id": sid, "reason": str(e)})

            if success_count > 0:
                await uow.commit()
                await self._refresh_stats(uow)

        return {
            "success_count": success_count,
            "failed_count": len(failed),
            "failed": failed,
        }

    async def bulk_delete(self, sefer_ids: List[int]) -> Dict[str, Any]:
        """
        Birden fazla seferi toplu sil.
        N+1 Transaction sorunu giderildi (Tek UoW).
        """
        success_count = 0
        failed = []

        async with UnitOfWork() as uow:
            for sid in sefer_ids:
                try:
                    success = await self._delete_sefer_uow(uow, sid)
                    if success:
                        success_count += 1
                    else:
                        failed.append(
                            {"id": sid, "reason": "Bulunamadı veya silinemedi"}
                        )
                except Exception as e:
                    logger.error(f"Bulk delete error for sid {sid}: {e}")
                    failed.append({"id": sid, "reason": str(e)})

            if success_count > 0:
                await uow.commit()
                await self._refresh_stats(uow)

        return {
            "success_count": success_count,
            "failed_count": len(failed),
            "failed": failed,
        }

    @audit_log("BULK_CREATE", "sefer", log_params=True)
    async def bulk_add_sefer(self, sefer_list: List[SeferCreate]) -> int:
        """Toplu sefer ekle (ELITE Performance: Batch Insert & Smart Enrichment)"""
        if not sefer_list:
            return 0

        count = 0
        from app.services.prediction_service import get_prediction_service

        pred_service = get_prediction_service()

        async with UnitOfWork() as uow:
            try:
                # 1. Pre-fetch Logic
                sorted_list = sorted(sefer_list, key=lambda x: (x.tarih, x.saat or ""))
                all_loc_names = await uow.lokasyon_repo.get_benzersiz_lokasyonlar()

                all_routes = await uow.lokasyon_repo.get_all(limit=1000)
                route_map = {
                    (
                        r["cikis_yeri"].upper().strip(),
                        r["varis_yeri"].upper().strip(),
                    ): r
                    for r in all_routes
                }

                items_to_add: List[Dict[str, Any]] = []

                for data in sorted_list:
                    if data.mesafe_km <= 0:
                        continue

                    matched_cikis = await uow.lokasyon_repo.find_closest_match(
                        data.cikis_yeri, pre_fetched_names=all_loc_names
                    )
                    if matched_cikis:
                        data.cikis_yeri = matched_cikis

                    matched_varis = await uow.lokasyon_repo.find_closest_match(
                        data.varis_yeri, pre_fetched_names=all_loc_names
                    )
                    if matched_varis:
                        data.varis_yeri = matched_varis

                    if data.cikis_yeri.lower() == data.varis_yeri.lower():
                        continue

                    route_key = (
                        data.cikis_yeri.upper().strip(),
                        data.varis_yeri.upper().strip(),
                    )
                    route_metadata = route_map.get(route_key)

                    if route_metadata:
                        if not data.ascent_m:
                            data.ascent_m = route_metadata.get("ascent_m", 0.0)
                        if not data.descent_m:
                            data.descent_m = route_metadata.get("descent_m", 0.0)
                        if not data.flat_distance_km:
                            data.flat_distance_km = route_metadata.get(
                                "flat_distance_km", 0.0
                            )
                        if not data.guzergah_id:
                            data.guzergah_id = route_metadata.get("id")

                    tahmini_tuk = None
                    try:
                        tonaj = data.ton or (
                            data.net_kg / 1000.0 if data.net_kg else 0.0
                        )
                        prediction = await pred_service.predict_consumption(
                            arac_id=data.arac_id,
                            mesafe_km=data.mesafe_km,
                            ton=tonaj,
                            ascent_m=data.ascent_m or 0.0,
                            descent_m=data.descent_m or 0.0,
                            flat_distance_km=data.flat_distance_km or 0.0,
                            sofor_id=data.sofor_id,
                            dorse_id=data.dorse_id,
                            target_date=data.tarih
                            if isinstance(data.tarih, date)
                            else date.fromisoformat(data.tarih),
                        )
                        if prediction and "prediction_liters" in prediction:
                            tahmini_tuk = float(prediction["prediction_liters"])
                    except Exception as pe:
                        logger.error(f"Bulk Prediction Error: {pe}")

                    items_to_add.append(
                        {
                            "tarih": data.tarih,
                            "saat": data.saat or "",
                            "arac_id": data.arac_id,
                            "dorse_id": data.dorse_id,
                            "sofor_id": data.sofor_id,
                            "guzergah_id": data.guzergah_id,
                            "net_kg": data.net_kg,
                            "ton": data.ton or round(data.net_kg / 1000, 2),
                            "bos_agirlik_kg": data.bos_agirlik_kg or 0,
                            "dolu_agirlik_kg": data.dolu_agirlik_kg or 0,
                            "cikis_yeri": data.cikis_yeri,
                            "varis_yeri": data.varis_yeri,
                            "mesafe_km": data.mesafe_km,
                            "bos_sefer": data.bos_sefer,
                            "ascent_m": data.ascent_m or 0.0,
                            "descent_m": data.descent_m or 0.0,
                            "flat_distance_km": data.flat_distance_km or 0.0,
                            "tahmini_tuketim": tahmini_tuk,
                            "durum": data.durum or "Tamam",
                            "notlar": data.notlar,
                            "sefer_no": data.sefer_no,
                        }
                    )

                if items_to_add:
                    await uow.sefer_repo.bulk_create(items_to_add)
                    count = len(items_to_add)
                    await uow.commit()
                    await self._refresh_stats(uow)

            except Exception as e:
                logger.error(f"Bulk insert hatası (Sefer): {e}")
                await uow.rollback()
                raise e

        return count

    @audit_log("CREATE_RETURN", "sefer")
    async def create_return_trip(
        self, sefer_id: int, user_id: Optional[int] = None
    ) -> int:
        """Mevcut seferden otomatik dönüş seferi oluşturur."""
        try:
            async with UnitOfWork() as uow:
                ref_sefer = await uow.sefer_repo.get_by_id(sefer_id)
                if not ref_sefer:
                    raise ValueError("Referans sefer bulunamadı")

            # Import SeferCreate model
            from app.schemas.sefer import SeferCreate
            from datetime import datetime

            base_sefer_no = ref_sefer.get("sefer_no")
            if base_sefer_no:
                # Prevent '-D-D' case
                if base_sefer_no.endswith("-D"):
                    base_sefer_no = base_sefer_no[:-2]
                return_sefer_no = f"{base_sefer_no}-D"
            else:
                return_sefer_no = None

            # Ters değerlerle SeferCreate oluştur
            new_data = SeferCreate(
                arac_id=ref_sefer.get("arac_id"),
                sofor_id=ref_sefer.get("sofor_id"),
                dorse_id=ref_sefer.get("dorse_id"),
                guzergah_id=ref_sefer.get("guzergah_id"),
                tarih=date.today(),
                saat=datetime.now().strftime("%H:%M"),
                cikis_yeri=ref_sefer.get("varis_yeri"),
                varis_yeri=ref_sefer.get("cikis_yeri"),
                mesafe_km=ref_sefer.get("mesafe_km", 1.0),
                sefer_no=return_sefer_no,
                bos_agirlik_kg=ref_sefer.get("bos_agirlik_kg", 0),
                dolu_agirlik_kg=ref_sefer.get("bos_agirlik_kg", 0),
                net_kg=0,
                ton=0.0,
                bos_sefer=True,
                durum="Planlandı",
                ascent_m=ref_sefer.get("descent_m", 0.0),
                descent_m=ref_sefer.get("ascent_m", 0.0),
                flat_distance_km=ref_sefer.get("flat_distance_km", 0.0),
                notlar=f"Dönüş seferi (Ref: #{sefer_id})",
                is_real=ref_sefer.get("is_real", False),
            )

            # add_sefer metodunu çağır
            return await self.add_sefer(new_data, user_id=user_id)

        except Exception as e:
            logger.error(f"Dönüş seferi oluşturma hatası: {e}")
            raise
