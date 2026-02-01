/**
 * Driver Service - Şoför yönetimi için API servisleri
 */
import { Driver } from '../types'
import { fetchWithAuth } from './api'

export const driverService = {
    /**
     * Tüm şoförleri getir
     */
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
        if (!response.ok) throw new Error('Şoförler alınamadı')
        return response.json() as Promise<Driver[]>
    },

    /**
     * Yeni şoför oluştur
     */
    create: async (data: Driver) => {
        const response = await fetchWithAuth('/drivers/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
        if (!response.ok) throw new Error('Şoför eklenemedi')
        return response.json() as Promise<Driver>
    },

    /**
     * Şoför güncelle
     */
    update: async (id: number, data: Partial<Driver>) => {
        const response = await fetchWithAuth(`/drivers/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        })
        if (!response.ok) throw new Error('Şoför güncellenemedi')
        return response.json() as Promise<Driver>
    },

    /**
     * Şoför sil (pasife çek)
     */
    delete: async (id: number) => {
        const response = await fetchWithAuth(`/drivers/${id}`, {
            method: 'DELETE',
        })
        if (!response.ok) throw new Error('Şoför silinemedi')
        return response.json() as Promise<Driver>
    },

    /**
     * Şoför puanı güncelle
     */
    updateScore: async (id: number, score: number) => {
        const response = await fetchWithAuth(`/drivers/${id}/score?score=${score}`, {
            method: 'POST',
        })
        if (!response.ok) throw new Error('Puan güncellenemedi')
        return response.json() as Promise<Driver>
    },

    /**
     * Excel'den toplu şoför yükle
     */
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

    /**
     * Excel şablonu indir (Blob döndürür)
     */
    downloadTemplate: async () => {
        const response = await fetchWithAuth('/drivers/excel/template')
        if (!response.ok) throw new Error('Şablon indirilemedi')
        return response.blob()
    },

    /**
     * Şoförleri Excel'e aktar (Blob döndürür)
     */
    exportToExcel: async (params: {
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
