import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { toast } from 'sonner';

/**
 * Kurumsal seviyede Axios örneği
 * - Otomatik Auth header ekleme
 * - 401 Unauthorized yönetimi (logout/redirect)
 * - Global hata yakalama ve kullanıcı bildirimi
 * - Request/Response logging (dev mode)
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const axiosInstance: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000, // 30 saniye
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request Interceptor: Token ekle
axiosInstance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token');
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response Interceptor: Hata yönetimi
axiosInstance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config;

        if (error.response) {
            const { status, data } = error.response;

            // 401: Oturum süresi dolmuş veya geçersiz
            if (status === 401 && !originalRequest?.url?.includes('/auth/token')) {
                localStorage.removeItem('access_token');
                if (window.location.pathname !== '/login') {
                    window.location.href = '/login';
                }
                return Promise.reject(new Error('Oturum süresi doldu, lütfen tekrar giriş yapın.'));
            }

            // 403: Yetkisiz erişim
            if (status === 403) {
                toast.error('Bu işlemi yapmak için yetkiniz bulunmamaktadır.');
            }

            // 422: Validasyon hataları
            if (status === 422) {
                const detail = (data as any)?.detail;
                if (Array.isArray(detail)) {
                    toast.error(detail[0]?.msg || 'Geçersiz veri girişi');
                } else {
                    toast.error(detail || 'Doğrulama hatası');
                }
            }

            // 500: Sunucu hataları
            if (status >= 500) {
                toast.error('Sunucu tarafında bir hata oluştu. Lütfen daha sonra tekrar deneyin.');
            }
        } else if (error.request) {
            // İstek yapıldı ama yanıt alınamadı (Network error vb.)
            toast.error('Sunucuya ulaşılamıyor. İnternet bağlantınızı kontrol edin.');
        }

        return Promise.reject(error);
    }
);

export default axiosInstance;
