/**
 * Güzergah (Location) Tipi
 */
export interface Location {
    id: number;
    cikis_yeri: string;
    varis_yeri: string;
    mesafe_km: number;
    tahmini_sure_saat: number;
    zorluk: 'Normal' | 'Orta' | 'Zor';
    ascent_m?: number;
    descent_m?: number;
    cikis_lat?: number;
    cikis_lon?: number;
    varis_lat?: number;
    varis_lon?: number;
    api_mesafe_km?: number;
    api_sure_saat?: number;
    flat_distance_km?: number;
    tahmini_yakit_lt?: number;
    last_api_call?: string;
    route_analysis?: RouteAnalysis;
    otoban_mesafe_km?: number;
    sehir_ici_mesafe_km?: number;
    notlar?: string;
    aktif?: boolean;
    source?: string;
    is_corrected?: boolean;
    correction_reason?: string;
}

/**
 * Güzergah Oluşturma Verisi
 */
export interface LocationCreate {
    cikis_yeri: string;
    varis_yeri: string;
    mesafe_km: number;
    tahmini_sure_saat?: number;
    zorluk?: 'Normal' | 'Orta' | 'Zor';
    ascent_m?: number;
    descent_m?: number;
    flat_distance_km?: number;
    cikis_lat?: number;
    cikis_lon?: number;
    varis_lat?: number;
    varis_lon?: number;
    otoban_mesafe_km?: number;
    sehir_ici_mesafe_km?: number;
    notlar?: string;
}

/**
 * Güzergah Güncelleme Verisi
 */
export interface LocationUpdate extends Partial<LocationCreate> { }

/**
 * Yükseklik Profili Noktası
 */
export interface ElevationPoint {
    distance_km: number;
    elevation_m: number;
}

export interface RouteAnalysis {
    highway: {
        flat: number;
        up: number;
        down: number;
    };
    other: {
        flat: number;
        up: number;
        down: number;
    };
    ratios?: {
        otoyol: number;
        devlet_yolu: number;
        sehir_ici: number;
    };
}

/**
 * OpenRouteService Analiz Yanıtı
 */
export interface AnalysisResponse {
    success: boolean;
    api_mesafe_km: number;
    api_sure_saat: number;
    ascent_m: number;
    descent_m: number;
    otoban_mesafe_km: number;
    sehir_ici_mesafe_km: number;
    elevation_profile: ElevationPoint[];
    route_analysis?: RouteAnalysis;
    source?: string;
    is_corrected?: boolean;
    correction_reason?: string;
}

