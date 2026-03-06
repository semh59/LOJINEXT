import axiosInstance from './axios-instance';
import { Vehicle, VehicleStats, PaginatedResponse } from '../../types';

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
    /**
     * Tüm araçları filtreler ile getirir
     */
    getAll: async (params: VehicleFilters = {}): Promise<PaginatedResponse<Vehicle>> => {
        const response = await axiosInstance.get<PaginatedResponse<Vehicle>>('/vehicles/', { params });
        return response.data;
    },

    /**
     * Tek bir araç detayı getirir
     */
    getById: async (id: number): Promise<Vehicle> => {
        const response = await axiosInstance.get<Vehicle>(`/vehicles/${id}`);
        return response.data;
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
        return response.data;
    },

    /**
     * Excel dosyası ile toplu araç yükler
     */
    uploadExcel: async (file: File): Promise<{ success: boolean; inserted: number; errors: any[] }> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await axiosInstance.post('/vehicles/upload', formData, {
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
