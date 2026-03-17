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
    }
};
