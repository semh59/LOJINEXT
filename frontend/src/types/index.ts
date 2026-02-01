
// Common Types

export interface User {
    id: number
    username: string
    full_name?: string
    role?: 'admin' | 'user' | 'readonly'
    is_active?: boolean
}

export interface DashboardStats {
    toplam_sefer: number
    toplam_km: number
    toplam_yakit: number
    filo_ortalama: number
    aktif_arac: number
    aktif_sofor: number
    bugun_sefer: number
    trends: {
        sefer: number
        km: number
        tuketim: number
    }
}

export interface Vehicle {
    id?: number
    plaka: string
    marka: string
    model: string
    yil: number
    tank_kapasitesi: number
    hedef_tuketim: number
    bos_agirlik_kg?: number
    hava_direnc_katsayisi?: number
    on_kesit_alani_m2?: number
    motor_verimliligi?: number
    lastik_direnc_katsayisi?: number
    maks_yuk_kapasitesi_kg?: number
    kapasite?: number // Yuk kapasitesi (kg)
    aktif: boolean
    notlar?: string
    created_at?: string
}

// Araç istatistikleri (detay modal için)
export interface VehicleStats extends Vehicle {
    toplam_sefer: number
    toplam_km: number
    ort_tuketim: number
}

export interface Driver {
    id?: number
    ad_soyad: string
    telefon?: string
    telefon_masked?: string
    ise_baslama?: string
    ehliyet_sinifi: 'B' | 'C' | 'CE' | 'D' | 'D1E' | 'E' | 'G'
    score: number
    manual_score: number
    aktif: boolean
    notlar?: string
    created_at?: string
}

export interface ApiError {
    detail: string | Array<{ msg: string }>
}

export interface Trip {
    id?: number
    tarih: string
    saat: string
    arac_id: number
    plaka?: string      // Join/Display (34ABC123)
    arac_plaka?: string // Legacy/Fallback alias
    sofor_id: number
    sofor_adi?: string  // Join/Display (Ad Soyad)
    sofor_ad_soyad?: string // Legacy/Fallback alias
    cikis_yeri: string
    varis_yeri: string
    mesafe_km: number
    net_kg: number
    ton?: number        // net_kg / 1000
    bos_sefer: boolean
    ascent_m?: number
    descent_m?: number
    baslangic_km?: number
    bitis_km?: number
    tuketim?: number    // L/100km
    dagitilan_yakit?: number
    durum: 'Tamam' | 'Devam Ediyor' | 'İptal' | 'Planlandı' | 'Yolda'
    created_at?: string
    notlar?: string
    guzergah_id?: number
    bos_agirlik_kg?: number
    dolu_agirlik_kg?: number
}

export interface Guzergah {
    id: number
    ad?: string
    cikis_yeri: string
    varis_yeri: string
    mesafe_km: number
    varsayilan_arac_id?: number
    varsayilan_sofor_id?: number
    varsayilan_arac_plaka?: string
    varsayilan_sofor_ad?: string
    notlar?: string
    aktif: boolean
    created_at?: string
}

export interface FuelRecord {
    id?: number
    tarih: string
    arac_id: number
    plaka?: string
    istasyon: string
    litre: number
    birim_fiyat: number
    toplam_tutar: number
    km_sayac: number
    fis_no?: string
    depo_durumu: 'Doldu' | 'Kısmi' | 'Bilinmiyor'
    durum?: 'Onaylandı' | 'Bekliyor' | 'Reddedildi'
    notlar?: string
}

export interface FuelStats {
    total_consumption: number
    total_cost: number
    avg_consumption: number
    avg_price: number
}

export interface CostAnalysis {
    month: string
    total: number
    fuel: number
    maintenance: number
}

export interface RoiStats {
    current_consumption: number
    target_consumption: number
    savings_amount: number
    annual_savings: number
    roi_percentage: number
}

export interface PredictionRequest {
    arac_id: number
    mesafe_km: number
    ton?: number
    ascent_m?: number
    descent_m?: number
    sofor_id?: number
    sofor_score?: number
    model_type?: 'linear' | 'xgboost'
}

export interface PredictionResponse {
    tahmini_tuketim: number
    model_used: 'linear' | 'xgboost'
    status?: 'success' | 'failure'
}

// Frontend için zenginleştirilmiş tahmin sonucu (opsiyonel alanlarla)
export interface PredictionResult extends PredictionResponse {
    guven_araligi?: { min: number; max: number }
    faktorler?: { name: string; impact: number }[]
    tasarruf_onerisi?: string
}

// Time Series Forecast
export interface ForecastResult {
    success: boolean
    forecast: number[]
    forecast_dates: string[]
    confidence_low: number[]
    confidence_high: number[]
    trend: 'increasing' | 'stable' | 'decreasing'
    vehicle_id?: number
}

// Trend Analysis
export interface TrendAnalysis {
    success: boolean
    trend: 'increasing' | 'stable' | 'decreasing'
    trend_tr: 'Artıyor' | 'Sabit' | 'Azalıyor'
    slope: number
    current_avg: number
    previous_avg: number
    moving_average_7?: number[]
}

// Ensemble Status
export interface EnsembleStatus {
    models: {
        physics: boolean
        lightgbm: boolean
        xgboost: boolean
        gradient_boosting: boolean
        random_forest: boolean
    }
    weights: Record<string, number>
    total_models: number
}

