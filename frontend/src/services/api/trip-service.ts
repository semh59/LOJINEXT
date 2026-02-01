import axiosInstance from './axios-instance';
import { Trip } from '../../types';

/**
 * Seferler (Trips) API Servisi
 */

export interface TripFilters {
    skip?: number;
    limit?: number;
    baslangic_tarih?: string;
    bitis_tarih?: string;
    arac_id?: number;
    sofor_id?: number;
    durum?: string;
    search?: string;
}

export const tripService = {
    /**
     * Tüm seferleri filtreler ile getirir
     */
    getAll: async (params: TripFilters = {}): Promise<Trip[]> => {
        const response = await axiosInstance.get<Trip[]>('/trips/', { params });
        return response.data;
    },

    /**
     * Tek bir sefer detayı getirir
     */
    getById: async (id: number): Promise<Trip> => {
        const response = await axiosInstance.get<Trip>(`/trips/${id}`);
        return response.data;
    },

    /**
     * Yeni sefer oluşturur
     */
    create: async (data: Omit<Trip, 'id' | 'created_at' | 'ton'>): Promise<Trip> => {
        const response = await axiosInstance.post<Trip>('/trips/', data);
        return response.data;
    },

    /**
     * Sefer günceller
     */
    update: async (id: number, data: Partial<Trip>): Promise<Trip> => {
        const response = await axiosInstance.put<Trip>(`/trips/${id}`, data);
        return response.data;
    },

    /**
     * Sefer siler (Soft delete)
     */
    delete: async (id: number): Promise<void> => {
        await axiosInstance.delete(`/trips/${id}`);
    },

    /**
     * Seferleri Excel olarak dışa aktarır
     */
    exportExcel: async (params: Omit<TripFilters, 'skip' | 'limit'> = {}): Promise<Blob> => {
        const response = await axiosInstance.get('/trips/excel/export', {
            params,
            responseType: 'blob',
        });
        return response.data;
    },

    /**
     * Excel dosyası ile toplu sefer yükler
     */
    uploadExcel: async (file: File): Promise<{ success: boolean; inserted: number; errors: any[] }> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await axiosInstance.post('/trips/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    /**
     * Bugünün aktif seferlerini getirir (Dashboard için)
     */
    getTodayTrips: async (): Promise<{ items: Trip[]; total: number }> => {
        const response = await axiosInstance.get('/trips/today');
        return response.data;
    },
};
