import { create } from 'zustand';
import { Trip } from '../types';
import { format, startOfMonth, endOfMonth } from 'date-fns';

interface TripFilters {
    durum: string;
    search: string;
    baslangic_tarih: string;
    bitis_tarih: string;
    arac_id?: number;
    sofor_id?: number;
}

interface TripState {
    // Data State
    filters: TripFilters;
    selectedTrip: Trip | null;
    viewMode: 'table' | 'grid';
    isFormOpen: boolean;

    // Actions
    setFilters: (filters: Partial<TripFilters>) => void;
    resetFilters: () => void;
    setSelectedTrip: (trip: Trip | null) => void;
    setViewMode: (mode: 'table' | 'grid') => void;
    toggleForm: (isOpen?: boolean) => void;
}

const initialFilters: TripFilters = {
    durum: '',
    search: '',
    baslangic_tarih: format(startOfMonth(new Date()), 'yyyy-MM-dd'),
    bitis_tarih: format(endOfMonth(new Date()), 'yyyy-MM-dd'),
};

export const useTripStore = create<TripState>((set) => ({
    // Initial State
    filters: initialFilters,
    selectedTrip: null,
    viewMode: 'table',
    isFormOpen: false,

    // Actions
    setFilters: (newFilters) =>
        set((state) => ({
            filters: { ...state.filters, ...newFilters },
        })),

    resetFilters: () => set({ filters: initialFilters }),

    setSelectedTrip: (trip) => set({ selectedTrip: trip }),

    setViewMode: (mode) => set({ viewMode: mode }),

    toggleForm: (isOpen) =>
        set((state) => ({
            isFormOpen: isOpen !== undefined ? isOpen : !state.isFormOpen,
            // Formu kapatırken seçili sefere de reset atalım (opsiyonel ama güvenli)
            selectedTrip: isOpen === false ? null : state.selectedTrip,
        })),
}));
