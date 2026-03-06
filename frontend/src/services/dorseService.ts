/**
 * Dorse Service - Dorse yönetimi için API servisleri
 */
import { Dorse } from '../types'
import { fetchWithAuth } from './api'

export interface StandardResponse<T> {
    data: T
    meta?: {
        count?: number
        offset?: number
        limit?: number
        total?: number
    }
    errors?: any[]
}

export const dorseService = {
    /**
     * Tüm dorseleri getir
     */
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
        if (params.min_yil) searchParams.append('min_yil', params.min_yil.toString())
        if (params.max_yil) searchParams.append('max_yil', params.max_yil.toString())

        const response = await fetchWithAuth(`/trailers/?${searchParams.toString()}`)
        if (!response.ok) throw new Error('Dorseler alınamadı')
        const result = await response.json() as StandardResponse<Dorse[]>
        return result.data
    },

    /**
     * Yeni dorse oluştur
     */
    create: async (data: Partial<Dorse>) => {
        const response = await fetchWithAuth('/trailers/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
        if (!response.ok) throw new Error('Dorse eklenemedi')
        const result = await response.json() as StandardResponse<Dorse>
        return result.data
    },

    /**
     * Dorse detayını getir
     */
    getById: async (id: number) => {
        const response = await fetchWithAuth(`/trailers/${id}`)
        if (!response.ok) throw new Error('Dorse detayı alınamadı')
        const result = await response.json() as StandardResponse<Dorse>
        return result.data
    },

    /**
     * Dorse güncelle
     */
    update: async (id: number, data: Partial<Dorse>) => {
        const response = await fetchWithAuth(`/trailers/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        })
        if (!response.ok) throw new Error('Dorse güncellenemedi')
        const result = await response.json() as StandardResponse<Dorse>
        return result.data
    },

    /**
     * Dorse sil
     */
    delete: async (id: number) => {
        const response = await fetchWithAuth(`/trailers/${id}`, {
            method: 'DELETE',
        })
        if (!response.ok) throw new Error('Dorse silinemedi')
        const result = await response.json() as StandardResponse<any>
        return result.data
    },

    /**
     * Excel olarak dışa aktar
     */
    exportExcel: async () => {
        const response = await fetchWithAuth('/trailers/export')
        if (!response.ok) throw new Error('Excel dışa aktarılamadı')
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `dorseler_${new Date().toISOString().split('T')[0]}.xlsx`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
    },

    /**
     * Şablon indir
     */
    downloadTemplate: async () => {
        const response = await fetchWithAuth('/trailers/template')
        if (!response.ok) throw new Error('Şablon indirilemedi')
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'dorse_sablonu.xlsx'
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
    },

    /**
     * Excel yükle (Import)
     */
    uploadExcel: async (file: File) => {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetchWithAuth('/trailers/import', {
            method: 'POST',
            body: formData,
        })

        if (!response.ok) throw new Error('Excel yüklenemedi')
        const result = await response.json() as StandardResponse<{ imported: number; errors: any[] }>
        return result.data
    }
}
