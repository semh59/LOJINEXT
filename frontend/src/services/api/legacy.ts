/**
 * API Service - Backend ile iletişim
 */
import { Vehicle } from '../../types'
import { storageService } from '../storage-service';

const API_BASE = '/api/v1'

// Token yönetimi
export const tokenStorage = {
    get: () => storageService.getItem<string>('access_token'),
    getRefreshToken: () => storageService.getItem<string>('refresh_token'),
    set: (accessToken: string, refreshToken?: string) => {
        storageService.setItem('access_token', accessToken)
        if (refreshToken) storageService.setItem('refresh_token', refreshToken)
    },
    setRefreshToken: (token: string) => {
        storageService.setItem('refresh_token', token)
    },
    remove: () => {
        storageService.removeItem('access_token')
        storageService.removeItem('refresh_token')
    },
    clear: () => {
        storageService.removeItem('access_token')
        storageService.removeItem('refresh_token')
    }
}

// Fetch wrapper with auth
// Fetch wrapper with auth
async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const token = tokenStorage.get()

    const headers = new Headers(options.headers)

    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    } else {
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
    }

    if (!response.ok) {
        console.error(`API Error: ${response.status} ${response.statusText}`, url)
        
        let errorMessage = response.statusText;
        try {
            // Clone response to avoid 'already consumed' if we need to log it later
            const errorData = await response.clone().json();
            
            if (typeof errorData.detail === 'string') {
                errorMessage = errorData.detail;
            } else if (Array.isArray(errorData.detail) && errorData.detail[0]?.msg) {
                // Validation errors: detail is an array
                errorMessage = errorData.detail[0].msg;
            } else if (errorData.message) {
                errorMessage = errorData.message;
            } else if (errorData.detail) {
                errorMessage = JSON.stringify(errorData.detail);
            }
        } catch {
            // No JSON body or parse error
        }

        if (response.status === 401) {
            console.error('[API] 401 Unauthorized - Token may be missing or invalid.', url);
            if (window.location.pathname !== '/login') {
                console.warn('[API] Redirecting to login due to 401');
                window.location.href = '/login'
            }
        }
        
        // Log response body for 422/500 errors
        try {
            const errBody = await response.text()
            console.error('API Error Body:', errBody.substring(0, 500))
        } catch (e) { /* ignore */ }
        
        throw new Error(errorMessage)
    } else {
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
        return data as { access_token: string; refresh_token: string; token_type: string }
    },

    refresh: async (refreshToken: string) => {
        const response = await fetch(`${API_BASE}/auth/refresh?refresh_token=${refreshToken}`, {
            method: 'POST',
        })

        if (!response.ok) {
            throw new Error('Oturum yenilenemedi')
        }

        return response.json() as Promise<{ access_token: string; refresh_token: string; token_type: string }>
    },

    getMe: async () => {
        const response = await fetchWithAuth('/auth/me')
        if (!response.ok) throw new Error('Kullanıcı bilgileri alınamadı')
        return response.json()
    },

    logout: async () => {
        try {
            await fetchWithAuth('/auth/logout', { method: 'POST' });
        } catch (e) {
            console.error('Backend logout failed:', e);
        }
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
        return response.json()
    },

    create: async (data: any) => {
        const response = await fetchWithAuth('/trips/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
        return response.json()
    },

    update: async (id: number, data: any) => {
        const response = await fetchWithAuth(`/trips/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        })
        return response.json()
    },

    delete: async (id: number) => {
        const response = await fetchWithAuth(`/trips/${id}`, {
            method: 'DELETE',
        })
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
    },
    import: async (file: File) => {
        return tripsApi.upload(file)
    },

    downloadTemplate: async () => {
        const response = await fetchWithAuth('/trips/excel/template')
        if (!response.ok) throw new Error('Şablon indirilemedi')
        return response.blob()
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
        // fetchWithAuth now handles error throwing with detail
        return response.json()
    },

    update: async (id: number, data: any) => {
        const response = await fetchWithAuth(`/drivers/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        })
        // fetchWithAuth now handles error throwing with detail
        return response.json()
    },

    delete: async (id: number) => {
        const response = await fetchWithAuth(`/drivers/${id}`, {
            method: 'DELETE',
        })
        // fetchWithAuth now handles error throwing with detail
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
    import: async (file: File) => {
        return driversApi.uploadExcel(file)
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
    import: async (file: File) => {
        return vehiclesApi.uploadExcel(file)
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
        return response.json()
    },

    create: async (data: any) => {
        const response = await fetchWithAuth('/fuel/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
        return response.json()
    },

    update: async (id: number, data: any) => {
        const response = await fetchWithAuth(`/fuel/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        })
        return response.json()
    },

    delete: async (id: number) => {
        const response = await fetchWithAuth(`/fuel/${id}`, {
            method: 'DELETE',
        })
        return response.json()
    },

    export: async (params: {
        baslangic_tarih?: string;
        bitis_tarih?: string;
        arac_id?: number;
    } = {}) => {
        const searchParams = new URLSearchParams()
        if (params.baslangic_tarih) searchParams.append('baslangic_tarih', params.baslangic_tarih)
        if (params.bitis_tarih) searchParams.append('bitis_tarih', params.bitis_tarih)
        if (params.arac_id) searchParams.append('arac_id', params.arac_id.toString())

        const response = await fetchWithAuth(`/fuel/excel/export?${searchParams.toString()}`)
        if (!response.ok) throw new Error('Dışa aktarma başarısız')
        return response.blob()
    },

    downloadTemplate: async () => {
        const response = await fetchWithAuth('/fuel/excel/template')
        if (!response.ok) throw new Error('Şablon indirilemedi')
        return response.blob()
    },

    uploadExcel: async (file: File) => {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetchWithAuth('/fuel/excel/upload', {
            method: 'POST',
            body: formData,
        })
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Dosya yüklenemedi')
        }
        return response.json()
    },
    import: async (file: File) => {
        return fuelApi.uploadExcel(file)
    },

    getStats: async (params: {
        baslangic_tarih?: string;
        bitis_tarih?: string;
        arac_id?: number;
    } = {}) => {
        const searchParams = new URLSearchParams()
        if (params.baslangic_tarih) searchParams.append('baslangic_tarih', params.baslangic_tarih)
        if (params.bitis_tarih) searchParams.append('bitis_tarih', params.bitis_tarih)
        if (params.arac_id) searchParams.append('arac_id', params.arac_id.toString())

        const response = await fetchWithAuth(`/fuel/stats?${searchParams.toString()}`)
        // Fallback mock if endpoint missing
        if (!response.ok) return { total_consumption: 0, total_cost: 0, avg_consumption: 0, avg_price: 0 }
        return response.json()
    }
}

// Reports API
export const reportsApi = {
    getCostAnalysis: async (months: number = 12) => {
        // Gerçek endpoint: /advanced-reports/cost/trend
        const response = await fetchWithAuth(`/advanced-reports/cost/trend?months=${months}`)
        if (!response.ok) {
            console.error('Cost analysis endpoint failed, returning empty array')
            return []
        }
        return response.json()
    },

    getRoiStats: async (investment: number) => {
        // Gerçek endpoint: /advanced-reports/cost/roi
        const response = await fetchWithAuth(`/advanced-reports/cost/roi?investment=${investment}`)
        if (!response.ok) {
            console.error('ROI endpoint failed')
            throw new Error('ROI analizi alınamadı')
        }
        return response.json()
    },

    getSavingsPotential: async (targetConsumption: number = 30) => {
        const response = await fetchWithAuth(`/advanced-reports/cost/savings-potential?target_consumption=${targetConsumption}`)
        if (!response.ok) throw new Error('Tasarruf potansiyeli alınamadı')
        return response.json()
    },

    getVehicleComparison: async (months: number = 3) => {
        const response = await fetchWithAuth(`/advanced-reports/cost/vehicle-comparison?months=${months}`)
        if (!response.ok) throw new Error('Araç karşılaştırması alınamadı')
        return response.json()
    },

    downloadPdf: async (type: string, id?: number, params: Record<string, string | number> = {}) => {
        // Build URL based on type
        let url = `/advanced-reports/pdf/${type.replace('_', '-')}`
        if (id) {
            url = `/advanced-reports/pdf/${type.split('_')[0]}/${id}`
        }

        const searchParams = new URLSearchParams()
        Object.entries(params).forEach(([key, val]) => {
            searchParams.append(key, val.toString())
        })

        const finalUrl = searchParams.toString() ? `${url}?${searchParams.toString()}` : url
        const response = await fetchWithAuth(finalUrl)
        if (!response.ok) throw new Error('PDF indirilemedi')
        return response.blob()
    },

    downloadExcel: async (type: string, params: Record<string, string | number> = {}) => {
        const searchParams = new URLSearchParams()
        searchParams.append('report_type', type)
        Object.entries(params).forEach(([key, val]) => {
            searchParams.append(key, val.toString())
        })

        const response = await fetchWithAuth(`/advanced-reports/excel/export?${searchParams.toString()}`)
        if (!response.ok) throw new Error('Excel dosyası indirilemedi')
        return response.blob()
    }
}

// AI Predictions API moved to prediction-service.ts


// Weather API
export const weatherApi = {
    getForecast: async (lat: number, lon: number) => {
        const response = await fetchWithAuth('/weather/forecast', {
            method: 'POST',
            body: JSON.stringify({ lat, lon })
        })
        if (!response.ok) throw new Error('Hava durumu alınamadı')
        return response.json()
    },
    getTripImpact: async (params: {
        cikis_lat: number;
        cikis_lon: number;
        varis_lat: number;
        varis_lon: number;
        trip_date?: string;
    }) => {
        const response = await fetchWithAuth('/weather/trip-impact', {
            method: 'POST',
            body: JSON.stringify(params)
        })
        if (!response.ok) throw new Error('Hava durumu etkisi hesaplanamadı')
        return response.json()
    },
    getDashboardSummary: async () => {
        const response = await fetchWithAuth('/weather/dashboard-summary')
        if (!response.ok) throw new Error('Hava durumu özeti alınamadı')
        return response.json()
    }
}

export const adminApi = {
    getConfigs: async (group?: string) => {
        const query = group ? `?group=${group}` : ''
        const response = await fetchWithAuth(`/admin/config/${query}`)
        if (!response.ok) throw new Error('Configs could not be loaded')
        return response.json()
    },

    getConfig: async (key: string) => {
        const response = await fetchWithAuth(`/admin/config/${key}`)
        if (!response.ok) throw new Error('Config could not be loaded')
        return response.json()
    },

    updateConfig: async (key: string, value: any, reason?: string) => {
        const response = await fetchWithAuth(`/admin/config/${key}`, {
            method: 'PUT',
            body: JSON.stringify({ value, reason })
        })
        if (!response.ok) throw new Error('Config could not be updated')
        return response.json()
    }
}

export const adminUsersApi = {
    getAll: async (skip: number = 0, limit: number = 100) => {
        const response = await fetchWithAuth(`/admin/users/?skip=${skip}&limit=${limit}`)
        if (!response.ok) throw new Error('Kullanıcılar alınamadı')
        return response.json()
    },
    create: async (data: any) => {
        const response = await fetchWithAuth(`/admin/users/`, {
            method: 'POST',
            body: JSON.stringify(data)
        })
        if (!response.ok) throw new Error('Kullanıcı oluşturulamadı')
        return response.json()
    },
    update: async (id: number, data: any) => {
        const response = await fetchWithAuth(`/admin/users/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        })
        if (!response.ok) throw new Error('Kullanıcı güncellenemedi')
        return response.json()
    },
    delete: async (id: number) => {
         const response = await fetchWithAuth(`/admin/users/${id}`, {
            method: 'DELETE'
        })
        if (!response.ok) throw new Error('Kullanıcı silinemedi')
        return response.json()
    }
}

export const adminMlApi = {
    triggerTraining: async (arac_id: number) => {
        const response = await fetchWithAuth(`/admin/ml/train/${arac_id}`, { method: 'POST' })
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || 'Model eğitimi başlatılamadı')
        }
        return response.json()
    },
    getQueue: async (limit: number = 50) => {
        const response = await fetchWithAuth(`/admin/ml/queue?limit=${limit}`)
        if (!response.ok) throw new Error('Eğitim kuyruğu alınamadı')
        return response.json()
    },
    getVersions: async (arac_id: number) => {
        const response = await fetchWithAuth(`/admin/ml/versions/${arac_id}`)
        if (!response.ok) throw new Error('Model versiyonları alınamadı')
        return response.json()
    }
}

export const adminImportsApi = {
    getHistory: async (limit: number = 50) => {
        const response = await fetchWithAuth(`/admin/imports/history?limit=${limit}`)
        if (!response.ok) throw new Error('Aktarım geçmişi alınamadı')
        return response.json()
    },
    rollback: async (job_id: number) => {
        const response = await fetchWithAuth(`/admin/imports/${job_id}/rollback`, { method: 'POST' })
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || 'Geri alma işlemi başarısız')
        }
        return response.json()
    }
}

export const adminMaintenanceApi = {
    getAlerts: async () => {
        const response = await fetchWithAuth(`/admin/maintenance/alerts`)
        if (!response.ok) throw new Error('Bakım uyarıları alınamadı')
        return response.json()
    },
    getHistory: async (arac_id: number) => {
        const response = await fetchWithAuth(`/admin/maintenance/${arac_id}`)
        if (!response.ok) throw new Error('Bakım geçmişi alınamadı')
        return response.json()
    },
    markComplete: async (bakim_id: number) => {
        const response = await fetchWithAuth(`/admin/maintenance/${bakim_id}/complete`, { method: 'PATCH' })
        if (!response.ok) throw new Error('Bakım durumu güncellenemedi')
        return response.json()
    },
    create: async (data: any) => {
        const response = await fetchWithAuth(`/admin/maintenance/`, {
            method: 'POST',
            body: JSON.stringify(data)
        })
        if (!response.ok) throw new Error('Bakım kaydı oluşturulamadı')
        return response.json()
    }
}

export const adminHealthApi = {
    getHealth: async () => {
        const response = await fetchWithAuth(`/admin/health/`)
        if (!response.ok) throw new Error('Sistem sağlığı verileri alınamadı')
        return response.json()
    },
    resetCircuitBreaker: async (serviceName: string) => {
        const response = await fetchWithAuth(`/admin/health/circuit-breaker/reset?service_name=${serviceName}`, { method: 'POST' })
        if (!response.ok) throw new Error('Devre kesici sıfırlanamadı')
        return response.json()
    },
    triggerBackup: async () => {
        const response = await fetchWithAuth(`/admin/health/backup/trigger`, { method: 'POST' })
        if (!response.ok) throw new Error('Yedekleme tetiklenemedi')
        return response.json()
    }
}

export const adminNotificationsApi = {
    getRules: async () => {
        const response = await fetchWithAuth(`/admin/notifications/rules`)
        if (!response.ok) throw new Error('Bildirim kuralları alınamadı')
        return response.json()
    },
    createRule: async (data: any) => {
        const response = await fetchWithAuth(`/admin/notifications/rules`, {
            method: 'POST',
            body: JSON.stringify(data)
        })
        if (!response.ok) throw new Error('Bildirim kuralı oluşturulamadı')
        return response.json()
    }
}

export { fetchWithAuth }
