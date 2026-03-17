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

export interface PredictionEnqueueResponse {
    task_id: string;
    status: string;
}

export interface PredictionStatusResponse {
    task_id: string;
    status: string;
    answer?: string;
    error?: string;
    finished_at?: string;
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
    },

    enqueue: async (payload: { question: string; context?: string }) => {
        const response = await axiosInstance.post<PredictionEnqueueResponse>('/predictions', payload);
        return response.data;
    },

    status: async (taskId: string) => {
        const response = await axiosInstance.get<PredictionStatusResponse>(`/predictions/${taskId}`);
        return response.data;
    },

    stream: (taskId: string, onMessage: (data: PredictionStatusResponse) => void) => {
        const source = new EventSource(`${axiosInstance.defaults.baseURL}/predictions/${taskId}/stream`, {
            withCredentials: true,
        });
        source.onmessage = (event) => {
            try {
                const parsed = JSON.parse(event.data) as PredictionStatusResponse;
                onMessage(parsed);
            } catch (err) {
                console.error('SSE parse error', err);
            }
        };
        return () => source.close();
    },
};
