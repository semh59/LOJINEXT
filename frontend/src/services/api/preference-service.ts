import axiosInstance from './axios-instance';

export interface Preference {
    id: number;
    modul: string;
    ayar_tipi: string;
    deger: any;
    ad?: string;
    is_default: boolean;
    created_at: string;
    updated_at: string;
}

export interface PreferenceCreate {
    modul: string;
    ayar_tipi: string;
    deger: any;
    ad?: string;
    is_default?: boolean;
}

export const preferenceService = {
    getPreferences: async (modul: string, ayar_tipi?: string) => {
        const response = await axiosInstance.get(`/preferences/${modul}${ayar_tipi ? `?ayar_tipi=${ayar_tipi}` : ''}`);
        return response.data.items as Preference[];
    },

    savePreference: async (data: PreferenceCreate) => {
        const response = await axiosInstance.post('/preferences/', data);
        return response.data as Preference;
    },

    deletePreference: async (id: number) => {
        const response = await axiosInstance.delete(`/preferences/${id}`);
        return response.data;
    },

    setDefault: async (id: number) => {
        const response = await axiosInstance.post(`/preferences/${id}/default`);
        return response.data;
    }
};
