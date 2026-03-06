
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
    kapasite?: number
    yakit_tipi: string
    hedef_tuketim: number
    aktif: boolean
    kilometre?: number
    current_lat?: number
    current_lon?: number
    last_update?: string
    motor_no?: string
    sasi_no?: string
    muayene_tarihi?: string
    sigorta_tarihi?: string
    tank_kapasitesi?: number
    maks_yuk_kapasitesi_kg?: number
    bos_agirlik_kg?: number
    hava_direnc_katsayisi?: number
    on_kesit_alani_m2?: number
    motor_verimliligi?: number
    lastik_direnc_katsayisi?: number
    notlar?: string
}

export interface Dorse {
    id?: number
    plaka: string
    marka?: string
    model?: string
    tipi: string
    dorse_tipi?: string
    yil?: number
    bos_agirlik_kg: number
    maks_yuk_kapasitesi_kg: number
    lastik_sayisi: number
    dorse_lastik_direnc_katsayisi?: number
    dorse_hava_direnci?: number
    rolling_resistance?: number
    drag_coefficient?: number
    muayene_tarihi?: string
    aktif: boolean
    notlar?: string
    created_at?: string
    updated_at?: string
}

export interface Driver {
    id?: number
    ad_soyad: string
    tc_no?: string
    telefon?: string
    ehliyet_sinifi: string
    kan_grubu?: string
    score: number
    aktif: boolean
    dogum_tarihi?: string
    ise_giris?: string
    ise_baslama?: string
    sofor_score?: number
    manuel_giris_serbest?: boolean
    davranis_skor?: number
    guvenlik_skor?: number
    verimlilik_skor?: number
    devir_skor?: number
    manual_score?: number
    notlar?: string
}

export interface FuelRecord {
    id?: number
    arac_id: number
    tarih: string
    litre: number
    fiyat_tl?: number
    toplam_tutar: number
    km_sayac: number
    fis_no?: string
    istasyon?: string
    depo_durumu: 'Doldu' | 'Kısmi'
    durum: 'Bekliyor' | 'Onaylandı' | 'Reddedildi'
    plaka?: string // Join result
    birim_fiyat?: number
}

export interface Guzergah {
    id?: number
    cikis_yeri: string
    varis_yeri: string
    mesafe_km: number
    tahmini_sure_dk?: number
    cikis_lat?: number
    cikis_lon?: number
    varis_lat?: number
    varis_lon?: number
    is_active: boolean
    varsayilan_arac_id?: number
    varsayilan_sofor_id?: number
    flat_distance_km?: number
    ad?: string
    aktif?: boolean
}

export interface Trip {
    id?: number
    arac_id: number
    sofor_id: number
    guzergah_id: number
    dorse_id?: number
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
    gercek_tuketim?: number
    tahmini_tuketim?: number
    is_real: boolean
    km_baslangic?: number
    km_bitis?: number
    ascent_m?: number
    descent_m?: number
    highway_km?: number
    city_km?: number
    flat_km?: number
    weather_impact?: number
    sofor_score?: number
    arac_plaka?: string
    sofor_ad_soyad?: string
    plaka?: string       // UI Alias
    sofor_adi?: string   // UI Alias
    rota_detay?: any     // UI Alias
    tuketim?: number     // UI Alias
    sefer_no?: string    // UI Alias
    bos_sefer?: boolean
    notlar?: string
    flat_distance_km?: number
    is_round_trip?: boolean
    return_net_kg?: number
    return_sefer_no?: string
    otoban_mesafe_km?: number
    sehir_ici_mesafe_km?: number
    duration_min?: number;
    predicted_duration_min?: number;
    arac?: Vehicle;
    sofor?: Driver;
    dorse?: Dorse;
}

export interface SeferTimelineItem {
    id: number
    zaman: string
    aksiyon: string
    aciklama?: string
    degisen_alanlar: string[]
    kullanici: string
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
    en_yuksek_eğim?: number
    yakit_verimliligi?: number
    toplam_maliyet?: number
    ort_tuketim?: number
    toplam_km?: number
}

export interface FuelStats {
    toplam_litre: number
    toplam_maliyet: number
    ort_tuketim: number
    toplam_km: number
    avg_price: number
    kayit_sayisi?: number
    ortalama_tuketim?: number
    tasarruf_miktari?: number
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
