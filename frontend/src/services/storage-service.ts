/**
 * Tip Güvenli LocalStorage Yönetim Servisi
 */

type StorageKey = 
    | 'access_token' 
    | 'refresh_token' 
    | 'user_prefs' 
    | 'theme' 
    | 'sidebar_state' 
    | 'last_trip_filters'
    | 'dashboard_order'
    | 'lojinext-trip-storage'
    | string;

export const storageService = {
    /**
     * Veri kaydet
     */
    setItem: <T>(key: StorageKey, value: T): void => {
        try {
            const serializedValue = typeof value === 'string' ? value : JSON.stringify(value);
            localStorage.setItem(key, serializedValue);
        } catch (error) {
            console.error(`[StorageService] Error saving ${key}:`, error);
        }
    },

    /**
     * Veri oku
     */
    getItem: <T>(key: StorageKey, defaultValue: T | null = null): T | null => {
        try {
            const value = localStorage.getItem(key);
            if (value === null) return defaultValue;

            // JSON parse denemesi
            try {
                return JSON.parse(value) as T;
            } catch {
                return value as unknown as T;
            }
        } catch (error) {
            console.error(`[StorageService] Error reading ${key}:`, error);
            return defaultValue;
        }
    },

    /**
     * Veri sil
     */
    removeItem: (key: StorageKey): void => {
        localStorage.removeItem(key);
    },

    /**
     * Tümünü temizle (dikkatli kullan)
     */
    clear: (): void => {
        localStorage.clear();
    },

    /**
     * User-scoped key oluştur (B-007 Fix)
     */
    getUserScopedKey: (key: string): string => {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return `${key}-anon`;
            const payload = JSON.parse(atob(token.split('.')[1]));
            const userId = payload.sub || payload.user_id || 'anon';
            return `${key}-${userId}`;
        } catch {
            return `${key}-anon`;
        }
    }
};
