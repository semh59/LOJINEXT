import axiosInstance from './axios-instance';
import { Vehicle, VehicleStats, PaginatedResponse } from '../../types';
import { validateResponse } from '../../lib/api-validator';
import { VehicleSchema, PaginatedResponseSchema, VehicleStatsSchema } from '../../schemas/entities';

/**
 * Araçlar (Vehicles) API Servisi
 */

export interface VehicleFilters {
    skip?: number;
    limit?: number;
    aktif_only?: boolean;
    search?: string;
    marka?: string;
    model?: string;
    min_yil?: number;
    max_yil?: number;
}

export const vehicleService = {
    getAll: async (params: VehicleFilters = {}): Promise<PaginatedResponse<Vehicle>> => {
        const response = await axiosInstance.get<Record<string, unknown>>('/vehicles/', { params });
        let result: PaginatedResponse<Vehicle>;

        // Handle standardized response { data, meta }
        if (response.data && response.data.data !== undefined) {
            result = {
                items: response.data.data as Vehicle[],
                total: (response.data.meta as Record<string, number>)?.total ?? (response.data.data as Vehicle[]).length
            };
        }
        // Fallback for raw list (old behavior)
        else if (Array.isArray(response.data)) {
            result = {
                items: response.data as Vehicle[],
                total: (response.data as Vehicle[]).length
            };
        } else {
            result = response.data as unknown as PaginatedResponse<Vehicle>;
        }

        return validateResponse(PaginatedResponseSchema(VehicleSchema), result, 'vehicleService.getAll');
    },

    /**
     * Tek bir araç detayı getirir
     */
    getById: async (id: number): Promise<Vehicle> => {
        const response = await axiosInstance.get<Vehicle>(`/vehicles/${id}`);
        return validateResponse(VehicleSchema, response.data, `vehicleService.getById(${id})`);
    },

    /**
     * Yeni araç oluşturur
     */
    create: async (data: Vehicle): Promise<Vehicle> => {
        const response = await axiosInstance.post<Vehicle>('/vehicles/', data);
        return response.data;
    },

    /**
     * Araç günceller
     */
    update: async (id: number, data: Partial<Vehicle>): Promise<Vehicle> => {
        const response = await axiosInstance.put<Vehicle>(`/vehicles/${id}`, data);
        return response.data;
    },

    /**
     * Araç siler
     */
    delete: async (id: number): Promise<void> => {
        await axiosInstance.delete(`/vehicles/${id}`);
    },

    /**
     * Araç istatistiklerini getirir
     */
    getStats: async (id: number): Promise<VehicleStats> => {
        const response = await axiosInstance.get<VehicleStats>(`/vehicles/${id}/stats`);
        return validateResponse(VehicleStatsSchema, response.data, `vehicleService.getStats(${id})`);
    },

    /**
     * Excel dosyası ile toplu araç yükler
     */
    uploadExcel: async (file: File): Promise<{ success: boolean; inserted: number; errors: unknown[] }> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await axiosInstance.post<{ success: boolean; inserted: number; errors: unknown[] }>('/vehicles/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    /**
     * Araçları Excel olarak dışa aktarır
     */
    exportExcel: async (params: Omit<VehicleFilters, 'skip' | 'limit'> = {}): Promise<Blob> => {
        const response = await axiosInstance.get('/vehicles/export', {
            params,
            responseType: 'blob',
        });
        return response.data;
    },

    /**
     * Excel şablonunu indirir
     */
    downloadTemplate: async (): Promise<Blob> => {
        const response = await axiosInstance.get('/vehicles/template', {
            responseType: 'blob',
        });
        return response.data;
    },
};
