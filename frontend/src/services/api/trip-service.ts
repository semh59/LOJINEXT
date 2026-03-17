import axiosInstance from './axios-instance';
import { Trip, SeferTimelineItem, FuelPerformanceAnalyticsResponse, TripStatsResponse } from '../../types';
import { validateResponse } from '../../lib/api-validator';
import { TripSchema, TripStatsSchema, SeferTimelineItemSchema } from '../../schemas/entities';

const TripPaginatedSchema = z.object({
    items: z.array(TripSchema),
    meta: z.object({
        total: z.number(),
        skip: z.number(),
        limit: z.number(),
    })
});

import { z } from 'zod';

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

export interface FuelPerformanceFilters extends TripFilters {}
export interface TripUploadResponse {
    success: boolean;
    total_rows: number;
    success_count: number;
    failed_count: number;
    errors: unknown[];
}

export const tripService = {
    /**
     * Tüm seferleri filtreler ile getirir
     */
    getAll: async (params: TripFilters = {}): Promise<TripListResponse> => {
        const cleanParams = Object.fromEntries(
            Object.entries(params).filter(([_, v]) => v != null && v !== '')
        );
        const response = await axiosInstance.get<Record<string, unknown>>('/trips/', { params: cleanParams });
        
        let result: TripListResponse;
        if (response.data && response.data.items !== undefined) {
             result = response.data as unknown as TripListResponse;
        } else {
             // Fallback for nested or different structures if any
             result = {
                 items: (response.data.data as Trip[]) ?? [],
                 meta: (response.data.meta as TripListResponse['meta']) ?? { total: 0, skip: 0, limit: 100 }
             };
        }

        return validateResponse(TripPaginatedSchema, result, 'tripService.getAll');
    },

    /**
     * Materialized View veya dinamik sorgu kullanarak sefer istatistiklerini getirir
     */
    getStats: async (params: { durum?: string; baslangic_tarih?: string; bitis_tarih?: string } = {}): Promise<TripStatsResponse> => {
        const cleanParams = Object.fromEntries(
            Object.entries(params).filter(([_, v]) => v != null && v !== '')
        );
        const response = await axiosInstance.get<TripStatsResponse>('/trips/stats', { params: cleanParams });
        return validateResponse(TripStatsSchema, response.data, 'tripService.getStats');
    },

    /**
     * Tek bir sefer detayı getirir
     */
    getById: async (id: number): Promise<Trip> => {
        const response = await axiosInstance.get<Trip>(`/trips/${id}`);
        return validateResponse(TripSchema, response.data, `tripService.getById(${id})`);
    },

    /**
     * Yeni sefer oluşturur (B-003: Idempotency key ile)
     */
    create: async (data: Omit<Trip, 'id' | 'created_at' | 'ton'>): Promise<Trip> => {
        const response = await axiosInstance.post<Trip>('/trips/', data, {
            headers: { 'X-Idempotency-Key': crypto.randomUUID() },
        });
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
        let items: SeferTimelineItem[] = [];
        if (Array.isArray(response.data)) {
            items = response.data as SeferTimelineItem[];
        } else {
            items = response.data?.items ?? [];
        }
        return validateResponse(z.array(SeferTimelineItemSchema), items, `tripService.getTimeline(${id})`);
    },

    /**
     * Seferler modulu icin yakit performansi analiz verisini getirir
     */
    getFuelPerformance: async (params: FuelPerformanceFilters = {}): Promise<FuelPerformanceAnalyticsResponse> => {
        const cleanParams = Object.fromEntries(
            Object.entries(params).filter(([_, v]) => v != null && v !== '')
        );
        const response = await axiosInstance.get<FuelPerformanceAnalyticsResponse>('/trips/analytics/fuel-performance', {
            params: cleanParams,
        });
        return response.data;
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
     * Excel dosyası ile toplu sefer yükler (B-003: Idempotency key ile)
     */
    uploadExcel: async (file: File): Promise<TripUploadResponse> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await axiosInstance.post('/trips/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
                'X-Idempotency-Key': crypto.randomUUID(),
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
    bulkDelete: async (ids: number[]): Promise<void> => {
        const response = await axiosInstance.post('/trips/bulk-delete', {
            sefer_ids: ids,
        });
        return response.data;
    },

    /**
     * Toplu durum günceller
     */
    bulkUpdateStatus: async (ids: number[], newStatus: string): Promise<void> => {
        const response = await axiosInstance.patch('/trips/bulk/status', {
            sefer_ids: ids,
            new_status: newStatus
        });
        return response.data;
    },

    /**
     * Toplu iptal eder
     */
    bulkCancel: async (ids: number[], reason: string): Promise<void> => {
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
