import axiosInstance from './axios-instance';
import { Trip, SeferTimelineItem } from '../../types';

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

export interface TripListResponse {
    items: Trip[];
    meta: {
        total: number;
        skip: number;
        limit: number;
    };
}

export interface TripStatsResponse {
    toplam_sefer: number;
    toplam_km: number;
    highway_km: number;
    total_ascent: number;
    total_weight: number;
    avg_highway_pct: number;
    last_updated: string | null;
}

export const tripService = {
    /**
     * Tüm seferleri filtreler ile getirir
     */
    getAll: async (params: TripFilters = {}): Promise<TripListResponse> => {
        const cleanParams = Object.fromEntries(
            Object.entries(params).filter(([_, v]) => v != null && v !== '')
        );
        const response = await axiosInstance.get<TripListResponse>('/trips/', { params: cleanParams });
        return response.data;
    },

    /**
     * Materialized View veya dinamik sorgu kullanarak sefer istatistiklerini getirir
     */
    getStats: async (params: { durum?: string; baslangic_tarih?: string; bitis_tarih?: string } = {}): Promise<TripStatsResponse> => {
        const cleanParams = Object.fromEntries(
            Object.entries(params).filter(([_, v]) => v != null && v !== '')
        );
        const response = await axiosInstance.get<TripStatsResponse>('/trips/stats', { params: cleanParams });
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
     * Mevcut bir seferden dönüş seferi oluşturur
     */
    createReturn: async (id: number): Promise<Trip> => {
        const response = await axiosInstance.post<Trip>(`/trips/${id}/return`);
        return response.data;
    },

    /**
     * Sefer günceller
     */
    update: async (id: number, data: Partial<Trip>): Promise<Trip> => {
        const response = await axiosInstance.patch<Trip>(`/trips/${id}`, data);
        return response.data;
    },

    /**
     * Sefer siler (Soft delete)
     */
    delete: async (id: number): Promise<void> => {
        await axiosInstance.delete(`/trips/${id}`);
    },

    /**
     * Seferin kronolojik olay akışını getirir
     */
    getTimeline: async (id: number): Promise<SeferTimelineItem[]> => {
        const response = await axiosInstance.get(`/trips/${id}/timeline`);
        return response.data.items;
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
     * Excel şablonunu indirir
     */
    downloadTemplate: async (): Promise<Blob> => {
        const response = await axiosInstance.get('/trips/excel/template', {
            responseType: 'blob',
        });
        return response.data;
    },

    /**
     * Toplu sefer siler
     */
    bulkDelete: async (ids: number[]): Promise<any> => {
        const response = await axiosInstance.delete('/trips/bulk', { 
            params: { sefer_ids: ids },
            paramsSerializer: {
                indexes: null // sefer_ids=1&sefer_ids=2 formatı
            }
        });
        return response.data;
    },

    /**
     * Toplu durum günceller
     */
    bulkUpdateStatus: async (ids: number[], newStatus: string): Promise<any> => {
        const response = await axiosInstance.patch('/trips/bulk/status', {
            sefer_ids: ids,
            new_status: newStatus
        });
        return response.data;
    },

    /**
     * Toplu iptal eder
     */
    bulkCancel: async (ids: number[], reason: string): Promise<any> => {
        const response = await axiosInstance.patch('/trips/bulk/cancel', {
            sefer_ids: ids,
            iptal_nedeni: reason
        });
        return response.data;
    },

    /**
     * Bugünün aktif seferlerini getirir (Dashboard için)
     */
    getTodayTrips: async (): Promise<{ items: Trip[]; total: number }> => {
        try {
            const response = await axiosInstance.get<TripListResponse>('/trips/today');
            return { items: response.data.items, total: response.data.meta.total };
        } catch (error) {
            console.warn('Today endpoint failed, falling back to filtered getAll', error);
            const today = new Date().toISOString().split('T')[0];
            const tripsData = await tripService.getAll({ baslangic_tarih: today, bitis_tarih: today });
            return { items: tripsData.items, total: tripsData.meta.total };
        }
    },
};
