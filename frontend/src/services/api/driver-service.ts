import axiosInstance from './axios-instance';
import { Driver } from '../../types';

/**
 * Şoförler (Drivers) API Servisi
 */

export interface DriverFilters {
    skip?: number;
    limit?: number;
    aktif_only?: boolean;
    search?: string;
    ehliyet_sinifi?: string;
    min_score?: number;
    max_score?: number;
}

export const driverService = {
    /**
     * Tüm şoförleri filtreler ile getirir
     */
    getAll: async (params: DriverFilters = {}): Promise<Driver[]> => {
        const response = await axiosInstance.get<Driver[]>('/drivers/', { params });
        return response.data;
    },

    /**
     * Tek bir şoför detayı getirir
     */
    getById: async (id: number): Promise<Driver> => {
        const response = await axiosInstance.get<Driver>(`/drivers/${id}`);
        return response.data;
    },

    /**
     * Yeni şoför oluşturur
     */
    create: async (data: any): Promise<Driver> => {
        const response = await axiosInstance.post<Driver>('/drivers/', data);
        return response.data;
    },

    /**
     * Şoför günceller
     */
    update: async (id: number, data: Partial<Driver>): Promise<Driver> => {
        const response = await axiosInstance.put<Driver>(`/drivers/${id}`, data);
        return response.data;
    },

    /**
     * Şoför siler
     */
    delete: async (id: number): Promise<void> => {
        await axiosInstance.delete(`/drivers/${id}`);
    },

    /**
     * Şoför puanı günceller
     */
    updateScore: async (id: number, score: number): Promise<any> => {
        const response = await axiosInstance.post(`/drivers/${id}/score`, null, {
            params: { score }
        });
        return response.data;
    },

    /**
     * Excel dosyası ile toplu şoför yükler
     */
    uploadExcel: async (file: File): Promise<{ success: boolean; inserted: number; errors: any[] }> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await axiosInstance.post('/drivers/excel/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    /**
     * Şoförleri Excel olarak dışa aktarır
     */
    exportExcel: async (params: Omit<DriverFilters, 'skip' | 'limit'> = {}): Promise<Blob> => {
        const response = await axiosInstance.get('/drivers/excel/export', {
            params,
            responseType: 'blob',
        });
        return response.data;
    },

    /**
     * Excel şablonunu indirir
     */
    downloadTemplate: async (): Promise<Blob> => {
        const response = await axiosInstance.get('/drivers/excel/template', {
            responseType: 'blob',
        });
        return response.data;
    },

    /**
     * Sürücü performans detaylarını getirir (AI Analizli)
     */
    getPerformance: async (id: number): Promise<any> => {
        const response = await axiosInstance.get(`/drivers/${id}/performance`)
        return response.data
    }
};
