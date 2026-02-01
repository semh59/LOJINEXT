import axiosInstance from './axios-instance';
import { Location, LocationCreate, LocationUpdate, AnalysisResponse } from '../../types/location';

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
    getAll: async (params: LocationFilters = {}): Promise<Location[]> => {
        const response = await axiosInstance.get<Location[]>('/locations/', { params });
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
    }
};
