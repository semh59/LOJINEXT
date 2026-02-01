import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
    Clock,
    Truck,
    MapPin,
    Navigation,
    Weight,
    Loader2,
    Route
} from 'lucide-react';

import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Trip, Guzergah } from '../../types';
import { vehiclesApi, driversApi, guzergahApi } from '../../services/api';
import { useQuery } from '@tanstack/react-query';

/**
 * Zod Şeması
 */
const tripSchema = z.object({
    tarih: z.string().min(1, 'Tarih gereklidir'),
    saat: z.string().min(1, 'Saat gereklidir'),

    // Coerce converts input string to number. 
    // We enforce min(1) but for initial state 0 is used, which might cause validation error immediately if we trigger it,
    // but defaultValues use 0. Ideally, we shouldn't validate on mount.
    arac_id: z.coerce.number().min(1, 'Araç seçimi gereklidir'),
    sofor_id: z.coerce.number().min(1, 'Şoför seçimi gereklidir'),
    guzergah_id: z.coerce.number().min(1, 'Güzergah seçimi ZORUNLUDUR'),

    cikis_yeri: z.string().min(2, 'Çıkış yeri en az 2 karakter olmalı'),
    varis_yeri: z.string().min(2, 'Varış yeri en az 2 karakter olmalı'),
    mesafe_km: z.coerce.number().min(1, 'Mesafe > 0 olmalı'),

    bos_agirlik_kg: z.coerce.number().min(0).default(0),
    dolu_agirlik_kg: z.coerce.number().min(0).default(0),
    net_kg: z.coerce.number().min(0).default(0),

    bos_sefer: z.boolean().default(false),
    ascent_m: z.coerce.number().default(0),
    descent_m: z.coerce.number().default(0),
    durum: z.enum(['Tamam', 'Devam Ediyor', 'İptal', 'Planlandı', 'Yolda', 'Bekliyor']).default('Tamam'),
    notlar: z.string().optional(),
});

type TripFormData = z.infer<typeof tripSchema>;

interface TripFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    initialData: Trip | null;
    onSubmit: (data: TripFormData) => void;
    isSubmitting: boolean;
}

export const TripFormModal: React.FC<TripFormModalProps> = ({
    isOpen,
    onClose,
    initialData,
    onSubmit,
    isSubmitting
}) => {
    const {
        register,
        handleSubmit,
        formState: { errors },
        watch,
        setValue,
        reset
    } = useForm<TripFormData>({
        resolver: zodResolver(tripSchema),
        defaultValues: {
            tarih: new Date().toISOString().split('T')[0],
            saat: new Date().toTimeString().slice(0, 5),
            arac_id: 0,
            sofor_id: 0,
            guzergah_id: 0,
            cikis_yeri: '',
            varis_yeri: '',
            mesafe_km: 0,
            bos_agirlik_kg: 0,
            dolu_agirlik_kg: 0,
            net_kg: 0,
            bos_sefer: false,
            ascent_m: 0,
            descent_m: 0,
            durum: 'Tamam',
            notlar: ''
        }
    });

    // --- DATA FETCHING ---
    const { data: routes } = useQuery({
        queryKey: ['routes', 'active'],
        queryFn: () => guzergahApi.getAll()
    });

    const { data: vehicles } = useQuery({
        queryKey: ['vehicles', 'active'],
        queryFn: () => vehiclesApi.getAll({ aktif_only: true })
    });

    const { data: drivers } = useQuery({
        queryKey: ['drivers', 'active'],
        queryFn: () => driversApi.getAll({ aktif_only: true })
    });

    // --- WATCHERS ---
    const watchedGuzergahId = watch('guzergah_id');
    const watchedBos = watch('bos_agirlik_kg');
    const watchedDolu = watch('dolu_agirlik_kg');

    // Auto-Calculate Net Weight
    useEffect(() => {
        const bos = Number(watchedBos || 0);
        const dolu = Number(watchedDolu || 0);
        // Sadece dolu > bos ise hesapla, yoksa 0 (ama negatif izin verilmese de mantıksal olarak)
        if (dolu > bos) {
            setValue('net_kg', dolu - bos);
        } else {
            setValue('net_kg', 0);
        }
    }, [watchedBos, watchedDolu, setValue]);

    // Handle Route Selection
    useEffect(() => {
        if (watchedGuzergahId && routes) {
            const selectedRoute = routes.find(r => r.id === Number(watchedGuzergahId));
            if (selectedRoute) {
                setValue('cikis_yeri', selectedRoute.cikis_yeri);
                setValue('varis_yeri', selectedRoute.varis_yeri);
                setValue('mesafe_km', selectedRoute.mesafe_km);

                if (selectedRoute.varsayilan_arac_id) {
                    setValue('arac_id', selectedRoute.varsayilan_arac_id);
                }
                if (selectedRoute.varsayilan_sofor_id) {
                    setValue('sofor_id', selectedRoute.varsayilan_sofor_id);
                }
            }
        }
    }, [watchedGuzergahId, routes, setValue]);

    // Initial Data
    useEffect(() => {
        if (initialData && isOpen) {
            // Edit Mode
            reset({
                tarih: initialData.tarih || new Date().toISOString().split('T')[0],
                saat: initialData.saat?.slice(0, 5) || '12:00',
                arac_id: initialData.arac_id || 0,
                sofor_id: initialData.sofor_id || 0,
                guzergah_id: initialData.guzergah_id || 0,
                cikis_yeri: initialData.cikis_yeri || '',
                varis_yeri: initialData.varis_yeri || '',
                mesafe_km: initialData.mesafe_km || 0,
                bos_sefer: initialData.bos_sefer || false,
                durum: initialData.durum || 'Tamam',
                bos_agirlik_kg: initialData.bos_agirlik_kg || 0,
                dolu_agirlik_kg: initialData.dolu_agirlik_kg || 0,
                net_kg: initialData.net_kg || 0,
                ascent_m: initialData.ascent_m || 0,
                descent_m: initialData.descent_m || 0,
                notlar: initialData.notlar || ''
            });
        } else if (!initialData && isOpen) {
            // New Mode
            reset({
                tarih: new Date().toISOString().split('T')[0],
                saat: new Date().toTimeString().slice(0, 5),
                arac_id: 0,
                sofor_id: 0,
                guzergah_id: 0,
                cikis_yeri: '',
                varis_yeri: '',
                mesafe_km: 0,
                bos_sefer: false,
                durum: 'Tamam',
                bos_agirlik_kg: 0,
                dolu_agirlik_kg: 0,
                net_kg: 0,
                ascent_m: 0,
                descent_m: 0,
                notlar: ''
            });
        }
    }, [initialData, isOpen, reset]);


    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={initialData ? 'Seferi Güncelle' : 'Yeni Sefer Girişi'}
            size="lg"
        >
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 py-2">

                {/* 1. GÜZERGAH SEÇİMİ (ZORUNLU) */}
                <div className="bg-indigo-50/50 p-6 rounded-[24px] border border-indigo-100">
                    <label className="text-xs font-bold text-indigo-600 uppercase tracking-widest flex items-center gap-2 mb-3">
                        <Route className="w-4 h-4" />
                        Güzergah Seçimi (Zorunlu)
                    </label>
                    <div className="relative">
                        <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-indigo-400 z-10" />
                        <select
                            {...register('guzergah_id')}
                            className="w-full pl-10 h-12 rounded-xl border border-indigo-200 bg-white text-base font-bold text-indigo-900 focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none appearance-none"
                        >
                            <option value="0">Bir güzergah seçiniz...</option>
                            {routes?.map((r: Guzergah) => (
                                <option key={r.id} value={r.id}>
                                    {r.ad || `${r.cikis_yeri} - ${r.varis_yeri}`} ({r.mesafe_km} km)
                                </option>
                            ))}
                        </select>
                    </div>
                    {errors.guzergah_id && <p className="text-xs text-red-500 font-bold mt-2 ml-1">{errors.guzergah_id.message}</p>}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Sol Kolon */}
                    <div className="space-y-6">
                        {/* Zaman */}
                        <div className="space-y-4">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                <Clock className="w-3.5 h-3.5" /> Zaman Bilgisi
                            </h4>
                            <div className="grid grid-cols-2 gap-4">
                                <Input type="date" {...register('tarih')} error={!!errors.tarih} />
                                <Input type="time" {...register('saat')} error={!!errors.saat} />
                            </div>
                        </div>

                        {/* Araç/Şoför */}
                        <div className="space-y-4">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                <Truck className="w-3.5 h-3.5" /> Personel & Araç
                            </h4>
                            <select {...register('arac_id')} className="w-full h-11 rounded-xl border border-slate-200 px-3 text-sm font-semibold">
                                <option value="0">Araç Seç...</option>
                                {vehicles?.map((v: any) => <option key={v.id} value={v.id}>{v.plaka}</option>)}
                            </select>
                            {errors.arac_id && <p className="text-xs text-red-500">{errors.arac_id.message}</p>}

                            <select {...register('sofor_id')} className="w-full h-11 rounded-xl border border-slate-200 px-3 text-sm font-semibold">
                                <option value="0">Şoför Seç...</option>
                                {drivers?.map((d: any) => <option key={d.id} value={d.id}>{d.ad_soyad}</option>)}
                            </select>
                            {errors.sofor_id && <p className="text-xs text-red-500">{errors.sofor_id.message}</p>}
                        </div>
                    </div>

                    {/* Sağ Kolon */}
                    <div className="space-y-6">
                        {/* Detaylar (Readonly from Route mainly) */}
                        <div className="space-y-4">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                <Navigation className="w-3.5 h-3.5" /> Detaylar (Otomatik)
                            </h4>
                            <div className="grid grid-cols-2 gap-3">
                                <Input {...register('cikis_yeri')} placeholder="Çıkış" readOnly className="bg-slate-50 text-slate-500" />
                                <Input {...register('varis_yeri')} placeholder="Varış" readOnly className="bg-slate-50 text-slate-500" />
                            </div>
                            <Input type="number" {...register('mesafe_km')} placeholder="Mesafe" readOnly className="bg-slate-50 text-slate-500" />
                        </div>

                        {/* Ağırlık */}
                        <div className="bg-emerald-50/50 p-4 rounded-xl border border-emerald-100 space-y-3">
                            <h4 className="text-xs font-bold text-emerald-600 uppercase tracking-widest flex items-center gap-2">
                                <Weight className="w-3.5 h-3.5" /> Kantar / Ağırlık
                            </h4>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-[10px] font-bold text-slate-500 ml-1">Boş (kg)</label>
                                    <Input type="number" {...register('bos_agirlik_kg')} className="h-10" />
                                </div>
                                <div>
                                    <label className="text-[10px] font-bold text-slate-500 ml-1">Dolu (kg)</label>
                                    <Input type="number" {...register('dolu_agirlik_kg')} className="h-10" />
                                </div>
                            </div>
                            <div className="pt-2 border-t border-emerald-200/50 flex justify-between items-center">
                                <span className="text-xs font-bold text-emerald-700">Net Yük:</span>
                                <span className="text-lg font-black text-emerald-700">{Number(watch('net_kg') || 0).toLocaleString()} kg</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="flex justify-end gap-3 pt-6 border-t border-slate-100">
                    <Button type="button" variant="ghost" onClick={onClose}>Vazgeç</Button>
                    <Button type="submit" disabled={isSubmitting} className="bg-indigo-600 text-white">
                        {isSubmitting && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                        Kaydet
                    </Button>
                </div>

            </form>
        </Modal>
    );
};
