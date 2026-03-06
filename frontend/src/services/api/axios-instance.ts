import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { toast } from 'sonner';
import { tokenStorage } from './legacy';

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
    timeout: 120000, // 120 saniye (Yerel AI için yeterli pay)
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request Interceptor: Token ekle
axiosInstance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const token = tokenStorage.get();
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
                const refreshToken = localStorage.getItem('refresh_token');

                if (refreshToken && !(originalRequest as any)?._retry) {
                    (originalRequest as any)._retry = true;
                    try {
                        const response = await axios.post(`${API_BASE_URL}/auth/refresh?refresh_token=${refreshToken}`);
                        const { access_token, refresh_token } = response.data;

                        localStorage.setItem('access_token', access_token);
                        if (refresh_token) localStorage.setItem('refresh_token', refresh_token);

                        if (originalRequest && originalRequest.headers) {
                            originalRequest.headers.Authorization = `Bearer ${access_token}`;
                            return axiosInstance(originalRequest);
                        }
                    } catch (refreshError) {
                        console.error('Refresh token failed', refreshError);
                        // Refresh de patlarsa logout yap
                    }
                }

                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                if (window.location.pathname !== '/login') {
                    window.location.href = '/login';
                }
                return Promise.reject(new Error('Oturum süresi doldu, lütfen tekrar giriş yapın.'));
            }

            // 403: Yetkisiz erişim
            if (status === 403) {
                toast.error('Bu işlemi yapmak için yetkiniz bulunmamaktadır.');
            }

            // 400: Bad Request (İş mantığı hataları)
            if (status === 400) {
                const message = (data as any)?.error?.message || (data as any)?.detail || 'Geçersiz işlem';
                toast.error(message);
            }

            // 422: Validasyon hataları
            if (status === 422) {
                const error = (data as any)?.error;
                if (error && error.message) {
                    toast.error(error.message);
                } else {
                    const detail = (data as any)?.detail;
                    if (Array.isArray(detail)) {
                        toast.error(detail[0]?.msg || 'Geçersiz veri girişi');
                    } else {
                        toast.error(detail || 'Doğrulama hatası');
                    }
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
