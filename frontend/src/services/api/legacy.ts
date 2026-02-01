/**
 * API Service - Backend ile iletişim
 */
import { Vehicle } from '../../types'

const API_BASE = '/api/v1'

// Token yönetimi
export const tokenStorage = {
    get: () => localStorage.getItem('access_token'),
    set: (token: string) => localStorage.setItem('access_token', token),
    remove: () => localStorage.removeItem('access_token'),
}

// Fetch wrapper with auth
// Fetch wrapper with auth
async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const token = tokenStorage.get()

    const headers = new Headers(options.headers)

    if (token) {
        console.log(`[API] Authorization header set for ${url}`);
        headers.set('Authorization', `Bearer ${token}`);
    } else {
        console.warn(`[API] No token found in storage for ${url}`);
    }

    // Ensure JSON content type if not set (for POST/PUT) and not FormData
    if (!headers.has('Content-Type') &&
        !(options.body instanceof FormData)) {
        headers.set('Content-Type', 'application/json')
    }

    const response = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers,
    })

    // ADVANCED LOGGING
    if (response.redirected) {
        console.warn(`⚠️ API Redirect Detected! Original: ${url}, Final: ${response.url}. This may cause auth headers to be lost.`)
    }

    if (!response.ok) {
        console.error(`API Error: ${response.status} ${response.statusText}`, url)
        if (response.status === 401) {
            console.error('[API] 401 Unauthorized - Token may be missing or invalid.', url);
            // tokenStorage.remove() // Don't remove immediately to avoid race condition cascade
            if (window.location.pathname !== '/login') {
                console.warn('[API] Redirecting to login due to 401');
                window.location.href = '/login'
            }
            throw new Error('Oturum süresi doldu')
        }
        // Log response body for 422/500 errors if possible
        try {
            const errBody = await response.clone().text()
            console.error('API Error Body:', errBody.substring(0, 500))
        } catch (e) { /* ignore */ }
    } else {
        console.debug(`API Success: ${response.status} ${url}`)
    }

    return response
}

// Auth API
export const authApi = {
    login: async (username: string, password: string) => {
        const formData = new URLSearchParams()
        formData.append('username', username)
        formData.append('password', password)

        const response = await fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData,
        })

        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('Kullanıcı adı veya şifre hatalı')
            }
            throw new Error('Giriş yapılamadı')
        }

        const data = await response.json()
        return data as { access_token: string; token_type: string }
    },

    getMe: async () => {
        const response = await fetchWithAuth('/auth/me')
        if (!response.ok) throw new Error('Kullanıcı bilgileri alınamadı')
        return response.json()
    },
}

// Dashboard API
export const dashboardApi = {
    getStats: async () => {
        const response = await fetchWithAuth('/reports/dashboard')
        if (!response.ok) throw new Error('Dashboard verileri alınamadı')
        return response.json()
    },

    getConsumptionTrend: async () => {
        const response = await fetchWithAuth('/reports/consumption-trend')
        if (!response.ok) throw new Error('Tüketim trendi alınamadı')
        return response.json()
    },
}

// Alerts API
export const alertsApi = {
    getCount: async () => {
        const response = await fetchWithAuth('/alerts/count')
        if (!response.ok) throw new Error('Uyarı sayısı alınamadı')
        return response.json()
    },

    getUnread: async (limit = 10) => {
        const response = await fetchWithAuth(`/alerts/unread/?limit=${limit}`)
        if (!response.ok) throw new Error('Uyarılar alınamadı')
        return response.json()
    },
}

// Trips API
export const tripsApi = {
    getAll: async (params: {
        skip?: number;
        limit?: number;
        baslangic_tarih?: string;
        bitis_tarih?: string;
        arac_id?: number;
        sofor_id?: number;
        durum?: string;
    } = {}) => {
        const searchParams = new URLSearchParams()
        if (params.skip !== undefined) searchParams.append('skip', params.skip.toString())
        if (params.limit !== undefined) searchParams.append('limit', params.limit.toString())
        if (params.baslangic_tarih) searchParams.append('baslangic_tarih', params.baslangic_tarih)
        if (params.bitis_tarih) searchParams.append('bitis_tarih', params.bitis_tarih)
        if (params.arac_id) searchParams.append('arac_id', params.arac_id.toString())
        if (params.sofor_id) searchParams.append('sofor_id', params.sofor_id.toString())
        if (params.durum) searchParams.append('durum', params.durum)

        const response = await fetchWithAuth(`/trips/?${searchParams.toString()}`)
        if (!response.ok) throw new Error('Seferler alınamadı')
        return response.json()
    },

    create: async (data: any) => {
        const response = await fetchWithAuth('/trips/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Sefer eklenemedi')
        }
        return response.json()
    },

    update: async (id: number, data: any) => {
        const response = await fetchWithAuth(`/trips/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        })
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Sefer güncellenemedi')
        }
        return response.json()
    },

    delete: async (id: number) => {
        const response = await fetchWithAuth(`/trips/${id}`, {
            method: 'DELETE',
        })
        if (!response.ok) throw new Error('Sefer silinemedi')
        return response.json()
    },

    export: async (params: {
        baslangic_tarih?: string;
        bitis_tarih?: string;
        arac_id?: number;
        sofor_id?: number;
        durum?: string;
    } = {}) => {
        const searchParams = new URLSearchParams()
        if (params.baslangic_tarih) searchParams.append('baslangic_tarih', params.baslangic_tarih)
        if (params.bitis_tarih) searchParams.append('bitis_tarih', params.bitis_tarih)
        if (params.arac_id) searchParams.append('arac_id', params.arac_id.toString())
        if (params.sofor_id) searchParams.append('sofor_id', params.sofor_id.toString())
        if (params.durum) searchParams.append('durum', params.durum)

        const response = await fetchWithAuth(`/trips/excel/export?${searchParams.toString()}`)
        if (!response.ok) throw new Error('Excel dosyası indirilemedi')
        return response.blob()
    },

    upload: async (file: File) => {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetchWithAuth('/trips/upload', {
            method: 'POST',
            body: formData,
        })
        if (!response.ok) throw new Error('Dosya yüklenemedi')
        return response.json()
    }
}

// Drivers API
export const driversApi = {
    getAll: async (params: {
        skip?: number;
        limit?: number;
        aktif_only?: boolean;
        search?: string;
        ehliyet_sinifi?: string;
        min_score?: number;
        max_score?: number;
    } = {}) => {
        const searchParams = new URLSearchParams()
        if (params.skip !== undefined) searchParams.append('skip', params.skip.toString())
        if (params.limit !== undefined) searchParams.append('limit', params.limit.toString())
        if (params.aktif_only !== undefined) searchParams.append('aktif_only', params.aktif_only.toString())
        if (params.search) searchParams.append('search', params.search)
        if (params.ehliyet_sinifi) searchParams.append('ehliyet_sinifi', params.ehliyet_sinifi)
        if (params.min_score !== undefined) searchParams.append('min_score', params.min_score.toString())
        if (params.max_score !== undefined) searchParams.append('max_score', params.max_score.toString())

        const response = await fetchWithAuth(`/drivers/?${searchParams.toString()}`)
        if (!response.ok) throw new Error('Sürücüler alınamadı')
        return response.json()
    },

    create: async (data: any) => {
        const response = await fetchWithAuth('/drivers/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
        if (!response.ok) throw new Error('Sürücü eklenemedi')
        return response.json()
    },

    update: async (id: number, data: any) => {
        const response = await fetchWithAuth(`/drivers/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        })
        if (!response.ok) throw new Error('Sürücü güncellenemedi')
        return response.json()
    },

    delete: async (id: number) => {
        const response = await fetchWithAuth(`/drivers/${id}`, {
            method: 'DELETE',
        })
        if (!response.ok) throw new Error('Sürücü silinemedi')
        return response.json()
    },

    // Puan güncelleme (dedicated endpoint)
    updateScore: async (id: number, score: number) => {
        const response = await fetchWithAuth(`/drivers/${id}/score?score=${score}`, {
            method: 'POST',
        })
        if (!response.ok) throw new Error('Puan güncellenemedi')
        return response.json()
    },

    uploadExcel: async (file: File) => {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetchWithAuth('/drivers/excel/upload', {
            method: 'POST',
            body: formData,
        })
        if (!response.ok) throw new Error('Dosya yüklenemedi')
        return response.json()
    },

    // Excel şablonu indir
    downloadTemplate: async () => {
        const response = await fetchWithAuth('/drivers/excel/template')
        if (!response.ok) throw new Error('Şablon indirilemedi')
        return response.blob()
    },

    // Excel'e aktar
    export: async (params: {
        aktif_only?: boolean;
        search?: string;
        ehliyet_sinifi?: string;
        min_score?: number;
        max_score?: number;
    } = {}) => {
        const searchParams = new URLSearchParams()
        if (params.aktif_only !== undefined) searchParams.append('aktif_only', params.aktif_only.toString())
        if (params.search) searchParams.append('search', params.search)
        if (params.ehliyet_sinifi) searchParams.append('ehliyet_sinifi', params.ehliyet_sinifi)
        if (params.min_score !== undefined) searchParams.append('min_score', params.min_score.toString())
        if (params.max_score !== undefined) searchParams.append('max_score', params.max_score.toString())

        const response = await fetchWithAuth(`/drivers/excel/export?${searchParams.toString()}`)
        if (!response.ok) throw new Error('Dışa aktarma başarısız')
        return response.blob()
    }
}

// Vehicles API
export const vehiclesApi = {
    getAll: async (params: {
        skip?: number;
        limit?: number;
        aktif_only?: boolean;
        search?: string;
        marka?: string;
        model?: string;
        min_yil?: number;
        max_yil?: number;
    } = {}) => {
        const searchParams = new URLSearchParams()
        if (params.skip !== undefined) searchParams.append('skip', params.skip.toString())
        if (params.limit !== undefined) searchParams.append('limit', params.limit.toString())
        if (params.aktif_only !== undefined) searchParams.append('aktif_only', params.aktif_only.toString())
        if (params.search) searchParams.append('search', params.search)
        if (params.marka) searchParams.append('marka', params.marka)
        if (params.model) searchParams.append('model', params.model)
        if (params.min_yil !== undefined) searchParams.append('min_yil', params.min_yil.toString())
        if (params.max_yil !== undefined) searchParams.append('max_yil', params.max_yil.toString())

        const response = await fetchWithAuth(`/vehicles/?${searchParams.toString()}`)
        if (!response.ok) throw new Error('Araçlar alınamadı')
        return response.json()
    },

    create: async (data: Vehicle) => {
        const response = await fetchWithAuth('/vehicles/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        })
        if (!response.ok) throw new Error('Araç eklenemedi')
        return response.json()
    },

    update: async (id: number, data: Partial<Vehicle>) => {
        const response = await fetchWithAuth(`/vehicles/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        })
        if (!response.ok) throw new Error('Araç güncellenemedi')
        return response.json()
    },

    delete: async (id: number) => {
        const response = await fetchWithAuth(`/vehicles/${id}`, {
            method: 'DELETE',
        })
        if (!response.ok) throw new Error('Araç silinemedi')
        return response.json()
    },

    uploadExcel: async (file: File) => {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetchWithAuth('/vehicles/upload', {
            method: 'POST',
            body: formData,
        })
        if (!response.ok) throw new Error('Dosya yüklenemedi')
        return response.json()
    },

    export: async (params: {
        aktif_only?: boolean;
        search?: string;
        marka?: string;
        model?: string;
        min_yil?: number;
        max_yil?: number;
    } = {}) => {
        const searchParams = new URLSearchParams()
        if (params.aktif_only !== undefined) searchParams.append('aktif_only', params.aktif_only.toString())
        if (params.search) searchParams.append('search', params.search)
        if (params.marka) searchParams.append('marka', params.marka)
        if (params.model) searchParams.append('model', params.model)
        if (params.min_yil !== undefined) searchParams.append('min_yil', params.min_yil.toString())
        if (params.max_yil !== undefined) searchParams.append('max_yil', params.max_yil.toString())

        const response = await fetchWithAuth(`/vehicles/export?${searchParams.toString()}`)
        if (!response.ok) throw new Error('Excel dosyası indirilemedi')
        return response.blob()
    },

    downloadTemplate: async () => {
        const response = await fetchWithAuth('/vehicles/template', {
            method: 'GET',
        })
        if (!response.ok) throw new Error('Şablon indirilemedi')
        return response.blob()
    },

    getStats: async (id: number) => {
        const response = await fetchWithAuth(`/vehicles/${id}/stats`)
        if (!response.ok) throw new Error('Araç istatistikleri alınamadı')
        return response.json()
    },
}

// Fuel API
export const fuelApi = {
    getAll: async (params: {
        skip?: number;
        limit?: number;
        arac_id?: number;
        baslangic_tarih?: string;
        bitis_tarih?: string;
        durum?: string;
    } = {}) => {
        const searchParams = new URLSearchParams()
        if (params.skip !== undefined) searchParams.append('skip', params.skip.toString())
        if (params.limit !== undefined) searchParams.append('limit', params.limit.toString())
        if (params.arac_id) searchParams.append('arac_id', params.arac_id.toString())
        if (params.baslangic_tarih) searchParams.append('baslangic_tarih', params.baslangic_tarih)
        if (params.bitis_tarih) searchParams.append('bitis_tarih', params.bitis_tarih)
        if (params.durum) searchParams.append('durum', params.durum)

        const response = await fetchWithAuth(`/fuel/?${searchParams.toString()}`)
        if (!response.ok) throw new Error('Yakıt kayıtları alınamadı')
        return response.json()
    },

    create: async (data: any) => {
        const response = await fetchWithAuth('/fuel/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
        if (!response.ok) throw new Error('Yakıt kaydı eklenemedi')
        return response.json()
    },

    update: async (id: number, data: any) => {
        const response = await fetchWithAuth(`/fuel/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        })
        if (!response.ok) throw new Error('Yakıt kaydı güncellenemedi')
        return response.json()
    },

    delete: async (id: number) => {
        const response = await fetchWithAuth(`/fuel/${id}`, {
            method: 'DELETE',
        })
        if (!response.ok) throw new Error('Yakıt kaydı silinemedi')
        return response.json()
    },

    getStats: async (params: {
        baslangic_tarih?: string;
        bitis_tarih?: string;
    } = {}) => {
        const searchParams = new URLSearchParams()
        if (params.baslangic_tarih) searchParams.append('baslangic_tarih', params.baslangic_tarih)
        if (params.bitis_tarih) searchParams.append('bitis_tarih', params.bitis_tarih)

        const response = await fetchWithAuth(`/fuel/stats?${searchParams.toString()}`)
        // Fallback mock if endpoint missing
        if (!response.ok) return { total_consumption: 0, total_cost: 0, avg_consumption: 0, avg_price: 0 }
        return response.json()
    }
}

// Reports API
export const reportsApi = {
    getCostAnalysis: async (months: number = 12) => {
        const response = await fetchWithAuth(`/reports/cost-analysis?months=${months}`)
        if (!response.ok) {
            // Mock data
            return [
                { month: 'Oca', total: 45000, fuel: 30000, maintenance: 15000 },
                { month: 'Şub', total: 48000, fuel: 32000, maintenance: 16000 },
                { month: 'Mar', total: 42000, fuel: 28000, maintenance: 14000 },
                { month: 'Nis', total: 52000, fuel: 35000, maintenance: 17000 },
                { month: 'May', total: 49000, fuel: 33000, maintenance: 16000 },
                { month: 'Haz', total: 55000, fuel: 38000, maintenance: 17000 },
            ]
        }
        return response.json()
    },

    getRoiStats: async (investment: number) => {
        const response = await fetchWithAuth(`/reports/roi?investment=${investment}`)
        if (!response.ok) {
            // Mock data based on input
            return {
                current_consumption: 35.2,
                target_consumption: 30.0,
                savings_amount: 12500,
                annual_savings: 150000,
                roi_percentage: Math.min(150, (150000 / investment) * 100)
            }
        }
        return response.json()
    },

    downloadPdf: async (_type: string, _params: any = {}) => {
        // In real app, this would download a PDF blob
        await new Promise(resolve => setTimeout(resolve, 2000))
        return true
    }
}

// AI Predictions API
export const predictionsApi = {
    // Yakıt tüketim tahmini
    predict: async (data: {
        arac_id: number;
        mesafe_km: number;
        ton?: number;
        ascent_m?: number;
        descent_m?: number;
        sofor_id?: number;
        sofor_score?: number;
        model_type?: 'linear' | 'xgboost';
    }) => {
        const response = await fetchWithAuth('/predictions/predict', {
            method: 'POST',
            body: JSON.stringify({
                arac_id: data.arac_id,
                mesafe_km: data.mesafe_km,
                ton: data.ton ?? 0,
                ascent_m: data.ascent_m ?? 0,
                descent_m: data.descent_m ?? 0,
                sofor_id: data.sofor_id,
                sofor_score: data.sofor_score,
                model_type: data.model_type ?? 'linear'
            })
        })

        if (!response.ok) {
            const errorBody = await response.text()
            console.error('Prediction API error:', errorBody)
            throw new Error('Tahmin yapılamadı')
        }
        return response.json()
    },

    // Haftalık tahmin (Time Series)
    getForecast: async (arac_id?: number) => {
        const url = arac_id
            ? `/predictions/time-series/forecast?arac_id=${arac_id}`
            : '/predictions/time-series/forecast'
        const response = await fetchWithAuth(url)
        if (!response.ok) throw new Error('Tahmin grafiği alınamadı')
        return response.json()
    },

    // Trend analizi
    getTrend: async (arac_id?: number, days: number = 30) => {
        const params = new URLSearchParams()
        if (arac_id) params.append('arac_id', arac_id.toString())
        params.append('days', days.toString())

        const response = await fetchWithAuth(`/predictions/time-series/trend?${params}`)
        if (!response.ok) throw new Error('Trend analizi alınamadı')
        return response.json()
    },

    // Ensemble model durumu
    getEnsembleStatus: async () => {
        const response = await fetchWithAuth('/predictions/ensemble/status')
        if (!response.ok) throw new Error('Model durumu alınamadı')
        return response.json()
    },

    // Model eğitimi (Admin)
    trainModel: async (arac_id: number, model_type: 'linear' | 'xgboost' = 'xgboost') => {
        const response = await fetchWithAuth(`/predictions/train/${arac_id}?model_type=${model_type}`, {
            method: 'POST'
        })
        if (!response.ok) throw new Error('Model eğitilemedi')
        return response.json()
    }
}

export { fetchWithAuth }
