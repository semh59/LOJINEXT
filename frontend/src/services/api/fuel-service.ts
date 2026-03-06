import axiosInstance from './axios-instance';
import { FuelRecord, FuelStats } from '../../types';

/**
 * Yakıt Kayıtları (Fuel) API Servisi
 */

export interface FuelFilters {
    skip?: number;
    limit?: number;
    arac_id?: number;
    baslangic_tarih?: string;
    bitis_tarih?: string;
    durum?: string;
}

export const fuelService = {
    /**
     * Tüm yakıt kayıtlarını filtreler ile getirir
     */
    getAll: async (params: FuelFilters = {}): Promise<{ items: FuelRecord[], total: number }> => {
        const response = await axiosInstance.get<{ items: FuelRecord[], total: number }>('/fuel/', { params });
        return response.data;
    },

    /**
     * Yeni yakıt kaydı oluşturur
     */
    create: async (data: any): Promise<FuelRecord> => {
        const response = await axiosInstance.post<FuelRecord>('/fuel/', data);
        return response.data;
    },

    /**
     * Yakıt kaydı günceller
     */
    update: async (id: number, data: any): Promise<FuelRecord> => {
        const response = await axiosInstance.put<FuelRecord>(`/fuel/${id}`, data);
        return response.data;
    },

    /**
     * Yakıt kaydı siler
     */
    delete: async (id: number): Promise<void> => {
        await axiosInstance.delete(`/fuel/${id}`);
    },

    /**
     * Yakıt kayıtlarını Excel olarak dışa aktarır
     */
    exportExcel: async (params: Omit<FuelFilters, 'skip' | 'limit'> = {}): Promise<Blob> => {
        const response = await axiosInstance.get('/fuel/excel/export', {
            params,
            responseType: 'blob',
        });
        return response.data;
    },

    /**
     * Excel şablonunu indirir
     */
    downloadTemplate: async (): Promise<Blob> => {
        const response = await axiosInstance.get('/fuel/excel/template', {
            responseType: 'blob',
        });
        return response.data;
    },

    /**
     * Yakıt istatistiklerini getirir
     */
    getStats: async (params: Omit<FuelFilters, 'skip' | 'limit'> = {}): Promise<FuelStats> => {
        const response = await axiosInstance.get<FuelStats>('/fuel/stats', { params });
        return response.data;
    },

    /**
     * Excel dosyası ile toplu yakıt yükler
     */
    uploadExcel: async (file: File): Promise<{ success: boolean; inserted: number; errors: any[] }> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await axiosInstance.post('/fuel/excel/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },
};
