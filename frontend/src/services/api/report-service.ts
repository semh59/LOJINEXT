import axiosInstance from './axios-instance';
import { DashboardStats } from '../../types';

/**
 * Raporlar ve Dashboard API Servisi
 */

export const reportService = {
    /**
     * Dashboard özet istatistiklerini getirir
     */
    getDashboardStats: async (): Promise<DashboardStats> => {
        const response = await axiosInstance.get<DashboardStats>('/reports/dashboard');
        return response.data;
    },

    /**
     * Aylık tüketim trendini getirir
     */
    getConsumptionTrend: async (): Promise<any[]> => {
        const response = await axiosInstance.get('/reports/consumption-trend');
        return response.data;
    },
    
    /**
     * Anomali özetini getirir
     */
    getAnomalySummary: async (): Promise<any> => {
        const response = await axiosInstance.get('/anomalies/summary');
        return response.data;
    },

    /**
     * Anomali geçmişini getirir
     */
    getAnomalyHistory: async (limit: number = 10): Promise<any[]> => {
        const response = await axiosInstance.get('/anomalies/history', { params: { limit } });
        return response.data;
    }
};
