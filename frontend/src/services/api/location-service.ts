import axiosInstance from './axios-instance';
import { Location, LocationCreate, LocationUpdate, AnalysisResponse } from '../../types/location';

/**
 * Rota bilgisi yanıt tipi (OpenRouteService)
 */
export interface RouteInfoResponse {
    distance_km: number;
    duration_min: number;
    duration_hours: number;
    ascent_m: number;
    descent_m: number;
    flat_distance_km: number;
    otoban_mesafe_km: number;
    sehir_ici_mesafe_km: number;
    difficulty: string;
    geometry?: Record<string, unknown>;
    source: 'api' | 'cache' | 'offline_fallback';
    route_analysis?: {
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
    };
}

/**
 * Güzergahlar (Locations) API Servisi
 */

export interface LocationFilters {
    skip?: number;
    limit?: number;
    zorluk?: string;
    search?: string; // Backend'de tam desteklenmiyor olabilir ama UI için ekliyoruz
}

export const locationService = {
    /**
     * Tüm güzergahları filtreler ile getirir
     */
    getAll: async (params: LocationFilters = {}): Promise<{ items: Location[]; total: number }> => {
        const response = await axiosInstance.get<{ items: Location[]; total: number }>('/locations/', { 
            params: { ...params, limit: 500 } 
        });
        return response.data;
    },

    /**
     * Tek bir güzergah detayı getirir
     */
    getById: async (id: number): Promise<Location> => {
        const response = await axiosInstance.get<Location>(`/locations/${id}`);
        return response.data;
    },

    /**
     * Yeni güzergah oluşturur
     */
    create: async (data: LocationCreate): Promise<Location> => {
        const response = await axiosInstance.post<Location>('/locations/', data);
        return response.data;
    },

    /**
     * Güzergah günceller
     */
    update: async (id: number, data: LocationUpdate): Promise<Location> => {
        const response = await axiosInstance.put<Location>(`/locations/${id}`, data);
        return response.data;
    },

    /**
     * Güzergah siler
     */
    delete: async (id: number): Promise<void> => {
        await axiosInstance.delete(`/locations/${id}`);
    },

    /**
     * Güzergah Analizi (OpenRouteService)
     */
    analyze: async (id: number): Promise<AnalysisResponse> => {
        const response = await axiosInstance.post<AnalysisResponse>(`/locations/${id}/analyze`);
        return response.data;
    },

    /**
     * Benzersiz lokasyon isimlerini getirir (Autocomplete için)
     */
    getUniqueNames: async (): Promise<string[]> => {
        const response = await axiosInstance.get<string[]>('/locations/unique-names/');
        return response.data;
    },

    /**
     * Rota ile arama (Sefer formu için)
     */
    searchByRoute: async (cikis: string, varis: string): Promise<{ found: boolean; location: Location | null }> => {
        const response = await axiosInstance.get('/locations/search/by-route', {
            params: { cikis, varis }
        });
        return response.data;
    },

    /**
     * Rota bilgilerini koordinatlara göre çeker
     */
    getRouteInfo: async (params: {
        cikis_lat: number;
        cikis_lon: number;
        varis_lat: number;
        varis_lon: number;
    }): Promise<RouteInfoResponse> => {
        const response = await axiosInstance.get<RouteInfoResponse>('/locations/route-info', { params });
        return response.data;
    },

    /**
     * Excel şablonu indirir
     */
    downloadTemplate: async (): Promise<Blob> => {
        const response = await axiosInstance.get('/locations/excel/template', {
            responseType: 'blob'
        });
        return response.data;
    },

    /**
     * Excel ile toplu güzergah yükler
     */
    uploadExcel: async (file: File): Promise<{ count: number; errors: string[] }> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await axiosInstance.post<{ count: number; errors: string[] }>('/locations/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },

    /**
     * Excel olarak dışa aktar
     */
    exportExcel: async (): Promise<Blob> => {
        const response = await axiosInstance.get('/locations/excel/export', {
            responseType: 'blob'
        });
        return response.data;
    }
};
