import axiosInstance from './axios-instance';

export interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

export interface ChatRequest {
    message: string;
    history?: ChatMessage[];
}

export interface ChatResponse {
    response: string;
    timestamp: string;
}

export interface AIStatus {
    is_ready: boolean;
    progress: {
        status: string;
        percent: number;
        speed: string;
    };
}

export const aiApi = {
    /**
     * AI ile sohbet et
     */
    chat: async (data: ChatRequest): Promise<ChatResponse> => {
        const response = await axiosInstance.post<ChatResponse>('/ai/chat', data);
        return response.data;
    },

    /**
     * AI sistem durumunu al
     */
    getStatus: async (): Promise<AIStatus> => {
        const response = await axiosInstance.get<AIStatus>('/ai/status');
        return response.data;
    }
};
