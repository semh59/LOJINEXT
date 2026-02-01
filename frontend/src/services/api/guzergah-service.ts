import axiosInstance from './axios-instance';
import { Guzergah } from '../../types';

export const guzergahApi = {
    getAll: async () => {
        const { data } = await axiosInstance.get<Guzergah[]>('/guzergahlar/');
        return data; // Endpoint returns list directly
    },

    create: async (payload: Partial<Guzergah>) => {
        const { data } = await axiosInstance.post<Guzergah>('/guzergahlar/', payload);
        return data;
    },

    update: async (id: number, payload: Partial<Guzergah>) => {
        // Backend returns bool
        const { data } = await axiosInstance.put<boolean>(`/guzergahlar/${id}`, payload);
        return data;
    },

    delete: async (id: number) => {
        const { data } = await axiosInstance.delete<boolean>(`/guzergahlar/${id}`);
        return data;
    }
};
