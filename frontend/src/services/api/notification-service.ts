import axiosInstance from './axios-instance';

export interface Notification {
    id: number;
    baslik: string;
    icerik: string;
    olay_tipi: string;
    okundu: boolean;
    olusturma_tarihi: string;
}

export const notificationService = {
    /**
     * Kullanıcının bildirimlerini getirir.
     */
    getMyNotifications: async (): Promise<Notification[]> => {
        const response = await axiosInstance.get('/admin/notifications/my');
        return response.data;
    },

    /**
     * Bildirimi okundu olarak işaretler.
     */
    markAsRead: async (notificationId: number): Promise<void> => {
        await axiosInstance.patch(`/admin/notifications/${notificationId}/read`);
    },

    /**
     * Tüm bildirimleri okundu olarak işaretler.
     */
    markAllAsRead: async (): Promise<void> => {
        await axiosInstance.post('/admin/notifications/mark-all-read');
    }
};
