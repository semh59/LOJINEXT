import axiosInstance from './axios-instance';
import { Driver } from '../../types';
import { validateResponse } from '../../lib/api-validator';
import { DriverSchema, PaginatedResponseSchema } from '../../schemas/entities';
import { z } from 'zod';

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
    getAll: async (params: DriverFilters = {}): Promise<{ items: Driver[], total: number }> => {
        const response = await axiosInstance.get<Record<string, unknown>>('/drivers/', { params });
        let result: { items: Driver[], total: number };

        // Handle standardized response { data, meta }
        if (response.data && response.data.data !== undefined) {
            result = {
                items: response.data.data as Driver[],
                total: (response.data.meta as Record<string, number>)?.total ?? (response.data.data as Driver[]).length
            };
        }
        // Fallback for raw list
        else {
            result = {
                items: Array.isArray(response.data) ? response.data as Driver[] : [],
                total: Array.isArray(response.data) ? (response.data as Driver[]).length : 0
            };
        }

        return validateResponse(PaginatedResponseSchema(DriverSchema), result, 'driverService.getAll');
    },

    /**
     * Tek bir şoför detayı getirir
     */
    getById: async (id: number): Promise<Driver> => {
        const response = await axiosInstance.get<Driver>(`/drivers/${id}`);
        return validateResponse(DriverSchema, response.data, `driverService.getById(${id})`);
    },

    /**
     * Yeni şoför oluşturur
     */
    create: async (data: Partial<Driver>): Promise<Driver> => {
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
    updateScore: async (id: number, score: number): Promise<{ success: boolean; new_score: number }> => {
        const response = await axiosInstance.post<{ success: boolean; new_score: number }>(`/drivers/${id}/score`, null, {
            params: { score }
        });
        return response.data;
    },

    /**
     * Excel dosyası ile toplu şoför yükler
     */
    uploadExcel: async (file: File): Promise<{ success: boolean; inserted: number; errors: unknown[] }> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await axiosInstance.post<{ success: boolean; inserted: number; errors: unknown[] }>('/drivers/excel/upload', formData, {
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
        return validateResponse(z.any(), response.data, `driverService.getPerformance(${id})`);
    }
};
