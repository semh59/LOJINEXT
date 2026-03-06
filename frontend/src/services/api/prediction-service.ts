import axiosInstance from './axios-instance';

/**
 * AI Prediction Service - ML model interactions
 */

export interface PredictionComparisonResponse {
    mae: number;
    rmse: number;
    accuracy_distribution: {
        good: number;
        warning: number;
        error: number;
        good_pct: number;
        warning_pct: number;
        error_pct: number;
    };
    trend: Array<{
        date: string;
        actual: number;
        predicted: number;
    }>;
    total_compared: number;
}

export const predictionService = {
    /**
     * Get comparison of predicted vs actual consumption
     */
    getComparison: async (days: number = 30): Promise<PredictionComparisonResponse> => {
        const response = await axiosInstance.get<PredictionComparisonResponse>('/predictions/comparison', {
            params: { days }
        });
        return response.data;
    },

    /**
     * Get single prediction for a scenario
     */
    predict: async (data: any) => {
        const response = await axiosInstance.post('/predictions/predict', data);
        return response.data;
    },

    /**
     * Explain a prediction (XAI)
     */
    explain: async (data: any) => {
        const response = await axiosInstance.post('/predictions/explain', data);
        return response.data;
    }
};
