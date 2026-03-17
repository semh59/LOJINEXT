
export interface PaginatedResponse<T> {
    items: T[]
    total: number
    skip?: number
    limit?: number
}

export interface BaseFilters {
    skip?: number
    limit?: number
    search?: string
    aktif_only?: boolean
}

export interface Vehicle {
    id?: number
    plaka: string
    marka: string
    model: string
    yil: number
    kapasite?: number | null
    yakit_tipi: string
    hedef_tuketim: number
    aktif: boolean
    kilometre?: number | null
    current_lat?: number | null
    current_lon?: number | null
    last_update?: string | null
    motor_no?: string | null
    sasi_no?: string | null
    muayene_tarihi?: string | null
    sigorta_tarihi?: string | null
    tank_kapasitesi?: number | null
    maks_yuk_kapasitesi_kg?: number | null
    bos_agirlik_kg?: number | null
    hava_direnc_katsayisi?: number | null
    on_kesit_alani_m2?: number | null
    motor_verimliligi?: number | null
    lastik_direnc_katsayisi?: number | null
    notlar?: string | null
}

export interface Dorse {
    id?: number
    plaka: string
    marka?: string | null
    model?: string | null
    tipi: string
    dorse_tipi?: string | null
    yil?: number | null
    bos_agirlik_kg: number
    maks_yuk_kapasitesi_kg: number
    lastik_sayisi: number
    dorse_lastik_direnc_katsayisi?: number | null
    dorse_hava_direnci?: number | null
    rolling_resistance?: number | null
    drag_coefficient?: number | null
    muayene_tarihi?: string | null
    aktif: boolean
    notlar?: string | null
    created_at?: string | null
    updated_at?: string | null
}

export interface Driver {
    id?: number
    ad_soyad: string
    tc_no?: string | null
    telefon?: string | null
    ehliyet_sinifi: string
    kan_grubu?: string | null
    score: number
    aktif: boolean
    dogum_tarihi?: string | null
    ise_giris?: string | null
    ise_baslama?: string | null
    sofor_score?: number | null
    manuel_giris_serbest?: boolean | null
    davranis_skor?: number | null
    guvenlik_skor?: number | null
    verimlilik_skor?: number | null
    devir_skor?: number | null
    manual_score?: number | null
    notlar?: string | null
}

export interface FuelRecord {
    id?: number
    arac_id: number
    tarih: string
    litre: number
    fiyat_tl?: number | null
    toplam_tutar: number
    km_sayac: number
    fis_no?: string | null
    istasyon?: string | null
    depo_durumu: 'Doldu' | 'Kısmi'
    durum: 'Bekliyor' | 'Onaylandı' | 'Reddedildi'
    plaka?: string | null
    birim_fiyat?: number | null
}

export interface Guzergah {
    id?: number
    ad?: string
    cikis_yeri: string
    varis_yeri: string
    mesafe_km: number
    tahmini_sure_dk?: number
    tahmini_sure_saat?: number
    zorluk?: 'Normal' | 'Orta' | 'Zor'
    ascent_m?: number | null
    descent_m?: number | null
    cikis_lat?: number | null
    cikis_lon?: number | null
    varis_lat?: number | null
    varis_lon?: number | null
    api_mesafe_km?: number | null
    api_sure_saat?: number | null
    flat_distance_km?: number | null
    tahmini_yakit_lt?: number | null
    last_api_call?: string | null
    otoban_mesafe_km?: number | null
    sehir_ici_mesafe_km?: number | null
    notlar?: string | null
    is_active?: boolean
    aktif?: boolean
    varsayilan_arac_id?: number
    varsayilan_sofor_id?: number
}

export interface Trip {
    id?: number
    arac_id: number
    sofor_id: number
    guzergah_id: number
    dorse_id?: number | null
    cikis_yeri: string
    varis_yeri: string
    mesafe_km: number
    bos_agirlik_kg: number
    dolu_agirlik_kg: number
    net_kg: number
    ton: number
    tarih: string
    saat: string
    durum: 'Planlandı' | 'Devam Ediyor' | 'Tamamlandı' | 'İptal' | 'Tamam' | 'Bekliyor' | 'Yolda'
    gercek_tuketim?: number | null
    tahmini_tuketim?: number | null
    is_real: boolean
    km_baslangic?: number | null
    km_bitis?: number | null
    ascent_m?: number | null
    descent_m?: number | null
    highway_km?: number | null
    city_km?: number | null
    flat_km?: number | null
    weather_impact?: number | null
    sofor_score?: number | null
    arac_plaka?: string | null
    sofor_ad_soyad?: string | null
    plaka?: string | null
    sofor_adi?: string | null
    rota_detay?: any | null
    tuketim?: number | null
    sefer_no?: string | null
    bos_sefer?: boolean | null
    notlar?: string | null
    flat_distance_km?: number | null
    is_round_trip?: boolean | null
    return_net_kg?: number | null
    return_sefer_no?: string | null
    otoban_mesafe_km?: number | null
    sehir_ici_mesafe_km?: number | null
    duration_min?: number | null
    predicted_duration_min?: number | null
    arac?: Vehicle | null
    sofor?: Driver | null
    dorse?: Dorse | null
    version?: number | null
}

export interface TripFormData {
    tarih: string;
    saat: string;
    arac_id: number;
    sofor_id: number;
    guzergah_id: number;
    dorse_id?: number | null;
    cikis_yeri: string;
    varis_yeri: string;
    mesafe_km: number;
    bos_agirlik_kg: number;
    dolu_agirlik_kg: number;
    net_kg: number;
    ton?: number;
    sefer_no?: string;
    bos_sefer?: boolean;
    durum: 'Planlandı' | 'Devam Ediyor' | 'Tamam' | 'Tamamlandı' | 'İptal' | 'Bekliyor' | 'Yolda';
    notlar?: string;
    ascent_m?: number;
    descent_m?: number;
    flat_distance_km?: number;
    is_round_trip?: boolean;
    return_net_kg?: number;
    return_sefer_no?: string;
    is_real?: boolean;
}

export interface SeferTimelineItem {
    id: number
    zaman: string
    tip: 'CREATE' | 'UPDATE' | 'STATUS_CHANGE' | 'PREDICTION_REFRESH' | 'RECONCILIATION' | 'DELETE'
    ozet: string
    kullanici: string
    changes?: Array<{ alan: string; eski: unknown; yeni: unknown }> | null
    prediction?: {
        onceki_tahmini_tuketim?: number | null
        tahmini_tuketim?: number | null
        tahmin_meta?: {
            model_used?: string | null
            model_version?: string | null
            confidence_score?: number | null
            fallback_triggered?: boolean | null
        } | null
    } | null
    technical_details?: Record<string, unknown> | null
}

export interface TripStatsResponse {
    toplam_sefer: number;
    toplam_km: number;
    highway_km: number;
    total_ascent: number;
    total_weight: number;
    avg_highway_pct: number;
    last_updated: string | null;
}

// Stats & Dashboard
export interface DashboardStats {
    toplam_sefer: number
    toplam_km: number
    toplam_yakit: number
    filo_ortalama: number
    aktif_arac: number
    aktif_sofor: number
    bugun_sefer: number
    toplam_arac: number
    trends: {
        sefer: number
        km: number
        tuketim: number
    }
}

export interface VehicleStats {
    toplam_yol: number
    ortalama_tuketim: number
    toplam_sefer: number
    aktif_gun: number
    en_yuksek_eğim?: number | null
    yakit_verimliligi?: number | null
    toplam_maliyet?: number | null
    ort_tuketim?: number | null
    toplam_km?: number | null
}

export interface FuelStats {
    toplam_litre: number
    toplam_maliyet: number
    ort_tuketim: number
    toplam_km: number
    avg_price: number
    kayit_sayisi?: number | null
    ortalama_tuketim?: number | null
    tasarruf_miktari?: number | null
    // Aliases for compatibility
    total_consumption: number
    total_cost: number
    avg_consumption: number
    total_distance: number
}

// ML & Predictions
export interface PredictionRequest {
    arac_id: number
    mesafe_km: number
    ton?: number
    ascent_m?: number
    descent_m?: number
    sofor_id?: number
    sofor_score?: number
    flat_distance_km?: number
    model_type?: 'linear' | 'xgboost' | 'ensemble'
}

export type PredictionFeatures = PredictionRequest;

export interface PredictionResponse {
    tahmini_tuketim: number       // L/100km
    tahmini_litre?: number         // Toplam litre (mesafe bazlı)
    model_used: 'linear' | 'xgboost' | 'ensemble'
    status?: 'success' | 'failure'
    confidence_low?: number
    confidence_high?: number
    insight?: string
    faktorler?: Record<string, number>
}

export interface PredictionResult extends PredictionResponse {
    guven_araligi?: { min: number; max: number }
    tasarruf_onerisi?: string
}

export interface ForecastItem {
    date: string
    value: number
    confidence_low?: number
    confidence_high?: number
}

export interface ForecastResponseModel {
    success: boolean
    forecast: number[]
    forecast_dates: string[]
    confidence_low: number[]
    confidence_high: number[]
    trend: 'increasing' | 'stable' | 'decreasing'
    vehicle_id?: number
    series?: ForecastItem[] // Added for widget compatibility
}

export interface ChartData {
    name: string
    value: number | null
    forecast?: number
    confidenceLow?: number
    confidenceHigh?: number
    fullDate?: string
}

export type TrendResponseModel = TrendAnalysis;

export interface TrendAnalysis {
    success: boolean
    trend: 'increasing' | 'stable' | 'decreasing'
    trend_tr: 'Artıyor' | 'Sabit' | 'Azalıyor'
    slope: number
    current_avg: number
    previous_avg: number
    details?: Array<{
        date: string
        val: number
    }>
    forecast?: number[]
    confidence_high?: number[]
    confidence_low?: number[]
    dates?: string[]
}

export interface PredictionComparisonResponse {
    mae: number
    rmse: number
    total_compared: number
    accuracy_distribution: {
        good: number
        warning: number
        error: number
        good_pct: number
        warning_pct: number
        error_pct: number
    }
    trend: Array<{
        date: string
        actual: number
        predicted: number
    }>
}

export interface EnsembleStatus {
    models: {
        physics: boolean
        lightgbm: boolean
        xgboost: boolean
        gb: boolean
        rf: boolean
    }
    weights: Record<string, number>
    last_train?: string
}

// User & Auth
export interface User {
    id: number
    email?: string
    full_name: string
    username?: string
    ad?: string
    soyad?: string
    role: string
    is_active: boolean
    last_login?: string
}

// Location specific re-exports or types
export interface AnalysisResponse {
    found: boolean
    location?: {
        cikis_lat: number
        cikis_lon: number
        varis_lat: number
        varis_lon: number
    }
}

export interface CostAnalysis {
    total_cost: number
    cost_per_km: number
    fuel_cost_share: number
    maintenance_share: number
    driver_share: number
    other_share: number
    dates: string[]
    costs: number[]
}

export interface RoiStats {
    current_consumption: number
    target_consumption: number
    annual_savings: number
    roi_percentage: number
}

export interface FuelPerformanceAnalyticsResponse {
    kpis: {
        mae: number
        rmse: number
        total_compared: number
        high_deviation_ratio: number
    }
    trend: Array<{
        date: string
        actual: number
        predicted: number
    }>
    distribution: {
        good: number
        warning: number
        error: number
        good_pct: number
        warning_pct: number
        error_pct: number
    }
    outliers: any[]
    low_data?: boolean
}
