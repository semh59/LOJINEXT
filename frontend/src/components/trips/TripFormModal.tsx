import React, { useEffect, useState } from 'react';
import { useForm, FieldValues } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Clock,
    Truck,
    Navigation,
    MapPin,
    X,
    ArrowLeftRight,
    Weight,
    Route,
    History
} from 'lucide-react';

import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Trip, Guzergah } from '../../types';
import { vehiclesApi, driversApi, locationService, weatherApi } from '../../services/api';
import { dorseService } from '../../services/dorseService';
import { useQuery } from '@tanstack/react-query';
import { cn } from '../../lib/utils';
import { WeatherAnalysisCard } from '../weather/WeatherAnalysisCard';
import { TripTimeline } from './TripTimeline';
import { tripService } from '../../services/api/trip-service';

/**
 * Zod Şeması
 */
const tripSchema = z.object({
    tarih: z.string().min(1, 'Tarih gereklidir'),
    saat: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/, 'Geçersiz saat formatı (HH:mm)'),
    sefer_no: z.string().max(50, 'Max 50 karakter').optional().or(z.literal('')),

    arac_id: z.coerce.number().int().min(1, 'Araç seçimi gereklidir'),
    dorse_id: z.coerce.number().int().optional().or(z.literal(0)),
    sofor_id: z.coerce.number().int().min(1, 'Şoför seçimi gereklidir'),
    guzergah_id: z.coerce.number().int().min(0).optional().transform(v => (v === 0 || v === undefined) ? undefined : v),
    
    cikis_yeri: z.string().min(1, 'Çıkış yeri'), 
    varis_yeri: z.string().min(1, 'Varış yeri'),
    mesafe_km: z.coerce.number().min(0.1, 'Mesafe > 0 olmalı'),

    bos_agirlik_kg: z.coerce.number().min(0).default(0),
    dolu_agirlik_kg: z.coerce.number().min(0).default(0),
    net_kg: z.coerce.number().min(0).default(0),

    bos_sefer: z.boolean().default(false),
    ascent_m: z.coerce.number().default(0),
    descent_m: z.coerce.number().default(0),
    flat_distance_km: z.coerce.number().default(0),
    durum: z.enum(['Planlandı', 'Devam Ediyor', 'Tamam', 'Tamamlandı', 'İptal', 'Bekliyor', 'Yolda']).default('Tamam'),
    is_real: z.boolean().optional(),
    ton: z.coerce.number().optional(),
    notlar: z.string().optional(),
    
    is_round_trip: z.boolean().default(false),
    return_net_kg: z.coerce.number().min(0).default(0),
    return_sefer_no: z.string().optional(),
});

type TripFormData = z.infer<typeof tripSchema>;

interface TripFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    initialData: Trip | null;
    onSubmit: (data: TripFormData) => void;
    isSubmitting: boolean;
    initialTab?: 'details' | 'timeline';
    isReadOnly?: boolean;
}

export const TripFormModal: React.FC<TripFormModalProps> = ({
    isOpen,
    onClose,
    initialData,
    onSubmit,
    isSubmitting,
    initialTab = 'details',
    isReadOnly = false
}) => {
    // Tab and Timeline State
    const [activeTab, setActiveTab] = useState<'details' | 'timeline'>(initialTab);
    const [timeline, setTimeline] = useState<any[]>([]);
    const [isTimelineLoading, setIsTimelineLoading] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
        watch,
        setValue,
        reset
    } = useForm<TripFormData & FieldValues>({
        resolver: zodResolver(tripSchema) as any,
        defaultValues: {
            tarih: new Date().toISOString().split('T')[0],
            saat: new Date().toTimeString().slice(0, 5),
            sefer_no: '',
            arac_id: 0,
            dorse_id: 0,
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
            flat_distance_km: 0,
            durum: 'Tamam',
            notlar: '',
            is_round_trip: false,
            return_net_kg: 0,
            return_sefer_no: ''
        }
    });

    // Reset form when modal closes or initialData changes
    useEffect(() => {
        if (!isOpen) {
            reset({
                tarih: new Date().toISOString().split('T')[0],
                saat: new Date().toTimeString().slice(0, 5),
                sefer_no: '',
                arac_id: 0,
                dorse_id: 0,
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
                flat_distance_km: 0,
                durum: 'Tamam',
                notlar: '',
                is_round_trip: false,
                return_net_kg: 0,
                return_sefer_no: ''
            });
            setActiveTab('details');
        } else if (initialData) {
            reset(initialData as any);
        }
    }, [isOpen, initialData, reset]);

    // Load Timeline when tab changes
    useEffect(() => {
        if (isOpen && initialData?.id && activeTab === 'timeline') {
            const loadTimeline = async () => {
                setIsTimelineLoading(true);
                try {
                    const items = await tripService.getTimeline(initialData.id!);
                    setTimeline(items);
                } catch (error) {
                    console.error('Failed to load timeline', error);
                } finally {
                    setIsTimelineLoading(false);
                }
            };
            loadTimeline();
        }
    }, [isOpen, initialData?.id, activeTab]);

    const prefersReducedMotion = typeof window !== 'undefined' ? window.matchMedia('(prefers-reduced-motion: reduce)').matches : false;
    const transitionProps = prefersReducedMotion ? { duration: 0 } : { duration: 0.3 };

    // --- DATA FETCHING ---
    const [weatherImpact, setWeatherImpact] = useState<number | null>(null);
    const [weatherLoading, setWeatherLoading] = useState(false);
    const [returnType, setReturnType] = useState<'none' | 'empty' | 'loaded'>('none');

    useEffect(() => {
        if (returnType === 'none') {
            setValue('is_round_trip', false);
            setValue('return_net_kg', 0);
        } else if (returnType === 'empty') {
            setValue('is_round_trip', true);
            setValue('return_net_kg', 0);
        } else if (returnType === 'loaded') {
            setValue('is_round_trip', true);
        }
    }, [returnType, setValue]);

    const { data: routeData } = useQuery({
        queryKey: ['routes', 'all'],
        queryFn: () => locationService.getAll({ limit: 1000 })
    });
    const routes = Array.isArray(routeData) ? routeData : (routeData as any)?.items || [];

    const { data: vehicleData } = useQuery({
        queryKey: ['vehicles', 'active'],
        queryFn: () => vehiclesApi.getAll({ aktif_only: true })
    });
    const vehicles = Array.isArray(vehicleData) ? vehicleData : (vehicleData as any)?.data || (vehicleData as any)?.items || [];

    const { data: driverData } = useQuery({
        queryKey: ['drivers', 'active'],
        queryFn: () => driversApi.getAll({ aktif_only: true })
    });
    const drivers = Array.isArray(driverData) ? driverData : (driverData as any)?.data || (driverData as any)?.items || [];

    const { data: trailerData } = useQuery({
        queryKey: ['trailers', 'active'],
        queryFn: () => dorseService.getAll({ aktif_only: true })
    });
    const trailers = Array.isArray(trailerData) ? trailerData : (trailerData as any)?.data || (trailerData as any)?.items || [];

    const watchedGuzergahId = watch('guzergah_id');
    const watchedBos = watch('bos_agirlik_kg');
    const watchedDolu = watch('dolu_agirlik_kg');

    useEffect(() => {
        const bos = Number(watchedBos || 0);
        const dolu = Number(watchedDolu || 0);
        if (dolu > bos) {
            setValue('net_kg', dolu - bos);
        } else {
            setValue('net_kg', 0);
        }
    }, [watchedBos, watchedDolu, setValue]);

    useEffect(() => {
        if (watchedGuzergahId && routes) {
            const selectedRoute = (routes as Guzergah[]).find(r => r.id === Number(watchedGuzergahId));
            if (selectedRoute) {
                setValue('cikis_yeri', selectedRoute.cikis_yeri);
                setValue('varis_yeri', selectedRoute.varis_yeri);
                setValue('mesafe_km', selectedRoute.mesafe_km);
                setValue('flat_distance_km', selectedRoute.flat_distance_km || 0);

                if (selectedRoute.varsayilan_arac_id) {
                    const isAracActive = vehicles?.some((v: any) => v.id === selectedRoute.varsayilan_arac_id);
                    if (isAracActive) {
                        setValue('arac_id', selectedRoute.varsayilan_arac_id);
                    }
                }
                if (selectedRoute.varsayilan_sofor_id) {
                    const isSoforActive = drivers?.some((d: any) => d.id === selectedRoute.varsayilan_sofor_id);
                    if (isSoforActive) {
                        setValue('sofor_id', selectedRoute.varsayilan_sofor_id);
                    }
                }
            }
        }
    }, [watchedGuzergahId, routes, setValue]);

    const watchedTarih = watch('tarih');
    const watchedCikis = watch('cikis_yeri');
    const watchedVaris = watch('varis_yeri');

    useEffect(() => {
        if (watchedGuzergahId && watchedCikis && watchedVaris) {
            const timer = setTimeout(async () => {
                setWeatherLoading(true);
                try {
                    const res = await locationService.searchByRoute(watchedCikis, watchedVaris);
                    if (res.found && res.location?.cikis_lat) {
                        const imp = await weatherApi.getTripImpact({
                            cikis_lat: res.location.cikis_lat, cikis_lon: res.location.cikis_lon!,
                            varis_lat: res.location.varis_lat!, varis_lon: res.location.varis_lon!,
                            trip_date: watchedTarih
                        });
                        setWeatherImpact(imp.fuel_impact_factor);
                    } else setWeatherImpact(null);
                } catch { setWeatherImpact(null); } finally { setWeatherLoading(false); }
            }, 1000);
            return () => clearTimeout(timer);
        }
    }, [watchedGuzergahId, watchedCikis, watchedVaris, watchedTarih]);

    useEffect(() => {
        if (isOpen) {
            setActiveTab(initialTab); // Reset tab on open to requested one
            if (initialData) {
                reset({
                    tarih: initialData.tarih || new Date().toISOString().split('T')[0],
                    saat: initialData.saat?.slice(0, 5) || '12:00',
                    sefer_no: (initialData as any).sefer_no || '',
                    arac_id: initialData.arac_id || 0,
                    dorse_id: (initialData as any).dorse_id || 0,
                    sofor_id: initialData.sofor_id || 0,
                    guzergah_id: initialData.guzergah_id || 0,
                    cikis_yeri: initialData.cikis_yeri || '',
                    varis_yeri: initialData.varis_yeri || '',
                    mesafe_km: initialData.mesafe_km || 0,
                    bos_sefer: initialData.bos_sefer || false,
                    durum: ((initialData.durum as string) === 'Hata' ? 'Tamam' : initialData.durum) || 'Tamam',
                    bos_agirlik_kg: initialData.bos_agirlik_kg || 0,
                    dolu_agirlik_kg: initialData.dolu_agirlik_kg || 0,
                    net_kg: initialData.net_kg || 0,
                    ascent_m: initialData.ascent_m || 0,
                    descent_m: initialData.descent_m || 0,
                    flat_distance_km: initialData.flat_distance_km || 0,
                    notlar: initialData.notlar || '',
                    is_round_trip: (initialData as any).is_round_trip || false,
                    return_net_kg: (initialData as any).return_net_kg || 0,
                    return_sefer_no: (initialData as any).return_sefer_no || ''
                });

                const isRound = (initialData as any).is_round_trip;
                const retKg = (initialData as any).return_net_kg || 0;
                if (!isRound) setReturnType('none');
                else if (retKg === 0) setReturnType('empty');
                else setReturnType('loaded');
            } else {
                setReturnType('none');
                reset({
                    tarih: new Date().toISOString().split('T')[0],
                    saat: new Date().toTimeString().slice(0, 5),
                    sefer_no: '',
                    arac_id: 0,
                    dorse_id: 0,
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
                    flat_distance_km: 0,
                    notlar: '',
                    is_round_trip: false,
                    return_net_kg: 0,
                    return_sefer_no: ''
                });
            }
        }
    }, [initialData, isOpen, reset, initialTab]);

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={isReadOnly ? 'Sefer Detayları' : (initialData ? 'Seferi Güncelle' : 'Yeni Sefer Girişi')}
            size="lg"
        >
            <form 
                noValidate
                autoComplete="off"
                onSubmit={handleSubmit(
                    (data) => {
                        console.log('🚀 [FORM SUCCESS] Veri doğrulandı. API gönderiliyor...', data);
                        onSubmit(data);
                    },
                    (errors) => {
                        console.error('❌ [FORM ERROR] Validasyon hataları:', errors);
                        const fieldKeys = Object.keys(errors);
                        const errorMsg = fieldKeys.map(key => `${key}: ${(errors as any)[key].message}`).join(', ');
                        toast.error(`Eksik veya hatalı bilgi: ${fieldKeys.length} alan. (${fieldKeys.join(', ')})`, {
                            duration: 5000,
                            description: errorMsg
                        });
                    }
                )} 
                className="space-y-6 relative"
            >
                {initialData && (
                    <div className="flex p-1.5 bg-[#131c20] border border-[#23353b] rounded-2xl mb-6 relative z-20 shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
                        <button
                            type="button"
                            onClick={() => setActiveTab('details')}
                            className={cn(
                                "flex-1 flex items-center justify-center gap-2 py-3.5 text-xs font-black uppercase tracking-[0.1em] rounded-xl transition-all duration-200",
                                activeTab === 'details' 
                                    ? "bg-[#25d1f4] text-[#0a0f12] shadow-[0_0_15px_rgba(37,209,244,0.4)]" 
                                    : "text-slate-400 hover:text-white hover:bg-[#1a282d]"
                            )}
                        >
                            <Route className="w-4 h-4" />
                            SEFER DETAYI
                        </button>
                        <button
                            type="button"
                            onClick={() => setActiveTab('timeline')}
                            className={cn(
                                "flex-1 flex items-center justify-center gap-2 py-3.5 text-xs font-black uppercase tracking-[0.1em] rounded-xl transition-all duration-200",
                                activeTab === 'timeline' 
                                    ? "bg-[#25d1f4] text-[#0a0f12] shadow-[0_0_15px_rgba(37,209,244,0.4)]" 
                                    : "text-slate-400 hover:text-white hover:bg-[#1a282d]"
                            )}
                        >
                            <History className="w-4 h-4" />
                            TİMELİNE
                        </button>
                    </div>
                )}

                <div className={cn(
                    "space-y-6 transition-all duration-300",
                    isReadOnly && "opacity-100"
                )}>

                <AnimatePresence mode="wait">
                    {activeTab === 'details' ? (
                        <motion.div 
                            key="details"
                            initial={prefersReducedMotion ? { opacity: 1 } : { opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={prefersReducedMotion ? { opacity: 1 } : { opacity: 0, x: 10 }}
                            transition={transitionProps}
                            className="space-y-6"
                        >
                            <fieldset disabled={isReadOnly} className="space-y-6 border-none p-0 m-0">
                                {/* 1. GÜZERGAH SEÇİMİ (ZORUNLU) */}
                                <div className="bg-[#131c20] p-6 rounded-[24px] border border-[#23353b] shadow-lg group">
                                    <label className="text-xs font-black text-[#25d1f4] uppercase tracking-wider flex items-center gap-2 mb-4">
                                        <Route className="w-4 h-4" />
                                        Güzergah Seçimi
                                    </label>
                                    <div className="relative">
                                        <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 z-10" />
                                        <select
                                            {...register('guzergah_id')}
                                            className={cn(
                                                "w-full pl-12 h-14 rounded-xl border bg-[#0a0f12] text-white text-base font-bold transition-all outline-none appearance-none shadow-inner",
                                                watchedGuzergahId && !(routes as Guzergah[]).find(r => r.id === Number(watchedGuzergahId))?.aktif 
                                                    ? "border-rose-500 text-rose-500 focus:ring-2 focus:ring-rose-500/20" 
                                                    : "border-[#23353b] hover:border-[#38535d] focus:border-[#25d1f4] focus:ring-2 focus:ring-[#25d1f4]/20"
                                            )}
                                        >
                                            <option value="" className="text-slate-500">Güzergah arayın veya listeden seçin...</option>
                                            {routes?.map((r: Guzergah) => (
                                                <option key={r.id} value={r.id} className={!r.aktif ? "bg-red-900 text-white" : "bg-[#0a0f12] text-white"}>
                                                    {r.ad || `${r.cikis_yeri} - ${r.varis_yeri}`} {!r.aktif && "(Pasif)"} ({r.mesafe_km} km)
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    {errors.guzergah_id && (
                                        <p className="mt-2 text-xs text-rose-500 font-bold flex items-center gap-1">
                                            <X className="w-3.5 h-3.5" /> {(errors.guzergah_id as any).message || 'Güzergah seçimi zorunludur!'}
                                        </p>
                                    )}
                                    {watchedGuzergahId && !(routes as Guzergah[]).find(r => r.id === Number(watchedGuzergahId))?.aktif && (
                                        <p className="mt-4 text-xs font-bold text-rose-500 flex items-center gap-2 bg-rose-500/10 p-3 rounded-lg border border-rose-500/20">
                                            <X className="w-4 h-4" /> Dikkat: Seçilen güzergah sistemde pasif durumdadır.
                                        </p>
                                    )}
                                </div>

                                {/* ROUND TRIP SELECTOR (3-Way) - SOLID & HIGH CONTRAST */}
                                <div className="bg-[#0a0f12] p-2.5 rounded-[20px] flex flex-wrap md:flex-nowrap items-center border border-[#23353b] shadow-inner gap-3">
                                    <button
                                        type="button"
                                        onClick={() => setReturnType('none')}
                                        className={cn(
                                            "flex-1 min-w-[100px] flex items-center justify-center gap-2 py-4 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200 border-2",
                                            returnType === 'none' 
                                                ? "bg-slate-100 text-[#0a0f12] border-slate-100 shadow-[0_0_15px_rgba(255,255,255,0.1)]" 
                                                : "bg-[#131c20] text-slate-400 border-transparent hover:border-[#38535d] hover:text-white"
                                        )}
                                    >
                                        <ArrowLeftRight className="w-5 h-5" />
                                        TEK YÖN
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setReturnType('empty')}
                                        className={cn(
                                            "flex-1 min-w-[100px] flex items-center justify-center gap-2 py-4 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200 border-2",
                                            returnType === 'empty'
                                                ? "bg-[#25d1f4] text-[#0a0f12] border-[#25d1f4] shadow-[0_0_15px_rgba(37,209,244,0.2)]" 
                                                : "bg-[#131c20] text-slate-400 border-transparent hover:border-[#38535d] hover:text-white"
                                        )}
                                    >
                                        <ArrowLeftRight className="w-5 h-5" />
                                        BOŞ DÖNÜŞ
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setReturnType('loaded')}
                                        className={cn(
                                            "flex-1 min-w-[100px] flex items-center justify-center gap-2 py-4 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200 border-2",
                                            returnType === 'loaded'
                                                ? "bg-amber-500 text-[#0a0f12] border-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.2)]" 
                                                : "bg-[#131c20] text-slate-400 border-transparent hover:border-[#38535d] hover:text-white"
                                        )}
                                    >
                                        <Weight className="w-5 h-5" />
                                        DOLU DÖNÜŞ
                                    </button>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-6">
                                        <div className="bg-[#131c20] p-6 rounded-[24px] border border-[#23353b] space-y-5">
                                            <h4 className="text-xs font-black text-slate-300 uppercase tracking-widest flex items-center gap-2">
                                                <Clock className="w-4 h-4 text-[#25d1f4]" /> Takvim ve Saat
                                            </h4>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="space-y-1.5">
                                                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Tarih</label>
                                                    <Input type="date" {...register('tarih')} error={!!errors.tarih} className="bg-[#0a0f12] border-[#23353b] focus:border-[#25d1f4] h-12 text-white" />
                                                </div>
                                                <div className="space-y-1.5">
                                                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Saat</label>
                                                    <Input type="time" {...register('saat')} error={!!errors.saat} className="bg-[#0a0f12] border-[#23353b] focus:border-[#25d1f4] h-12 text-white" />
                                                </div>
                                            </div>
                                            <div className="space-y-1.5">
                                                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Sefer No (HBL/İş No)</label>
                                                <Input placeholder="Örn: SEF-2024-001" {...register('sefer_no')} error={!!errors.sefer_no} autoComplete="off" className="bg-[#0a0f12] border-[#23353b] focus:border-[#25d1f4] h-12 text-white" />
                                                {errors.sefer_no && <p className="text-xs text-red-500 font-bold">{errors.sefer_no.message as string}</p>}
                                            </div>
                                        </div>

                                        <div className="bg-[#131c20] p-6 rounded-[24px] border border-[#23353b] space-y-5">
                                            <h4 className="text-xs font-black text-slate-300 uppercase tracking-widest flex items-center gap-2">
                                                <Truck className="w-4 h-4 text-[#25d1f4]" /> Personel & Araç Seçimi
                                            </h4>
                                            <div className="space-y-4">
                                                <div className="space-y-1.5">
                                                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Araç Plakası</label>
                                                    <select {...register('arac_id')} className={cn(
                                                        "w-full h-12 rounded-xl border bg-[#0a0f12] px-4 text-sm font-bold transition-all outline-none appearance-none",
                                                        errors.arac_id ? "border-rose-500 text-rose-500 focus:border-rose-500" : "border-[#23353b] text-white focus:border-[#25d1f4]"
                                                    )}>
                                                        <option value="0" className="text-slate-500">Seçim Yapınız...</option>
                                                        {vehicles?.map((v: any) => <option key={v.id} value={v.id} className="bg-[#0a0f12] text-white">{v.plaka}</option>)}
                                                    </select>
                                                    {errors.arac_id && <p className="text-[10px] text-rose-500 font-bold">{(errors.arac_id as any).message}</p>}
                                                </div>
                                                <div className="space-y-1.5">
                                                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Dorse (Opsiyonel)</label>
                                                    <select {...register('dorse_id')} className="w-full h-12 rounded-xl border border-[#23353b] bg-[#0a0f12] px-4 text-sm font-bold text-white transition-all focus:border-[#25d1f4] outline-none appearance-none">
                                                        <option value="0" className="text-slate-500">Seçim Yok</option>
                                                        {trailers?.map((t: any) => <option key={t.id} value={t.id} className="bg-[#0a0f12] text-white">{t.plaka}</option>)}
                                                    </select>
                                                </div>
                                                <div className="space-y-1.5">
                                                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Sürücü Müsaitliği</label>
                                                    <select {...register('sofor_id')} className={cn(
                                                        "w-full h-12 rounded-xl border bg-[#0a0f12] px-4 text-sm font-bold transition-all outline-none appearance-none",
                                                        errors.sofor_id ? "border-rose-500 text-rose-500 focus:border-rose-500" : "border-[#23353b] text-white focus:border-[#25d1f4]"
                                                    )}>
                                                        <option value="0" className="text-slate-500">Şoför Ataması Yapınız...</option>
                                                        {drivers?.map((d: any) => <option key={d.id} value={d.id} className="bg-[#0a0f12] text-white">{d.ad_soyad}</option>)}
                                                    </select>
                                                    {errors.sofor_id && <p className="text-[10px] text-rose-500 font-bold">{(errors.sofor_id as any).message}</p>}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-6">
                                        <div className="bg-[#131c20] p-6 rounded-[24px] border border-[#23353b] space-y-4">
                                            <h4 className="text-xs font-black text-slate-300 uppercase tracking-widest flex items-center gap-2">
                                                <Navigation className="w-4 h-4 text-[#25d1f4]" /> Telemetri Özeti
                                            </h4>
                                            <WeatherAnalysisCard weatherImpact={weatherImpact} weatherLoading={weatherLoading} />
                                            {watchedGuzergahId ? (
                                                <div className="flex items-center justify-between p-5 bg-[#0a0f12] rounded-2xl border border-[#23353b]">
                                                    <div className="flex flex-col">
                                                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Çıkış Noktası</span>
                                                        <span className="font-black text-white text-sm">{watch('cikis_yeri')}</span>
                                                    </div>
                                                    <div className="flex flex-col items-center px-4 w-full">
                                                        <div className="w-full h-1 bg-[#23353b] rounded-full relative mb-1.5 flex justify-center items-center">
                                                            <div className="absolute inset-x-8 h-full bg-[#25d1f4]/30 rounded-full" />
                                                            <div className="absolute h-2 w-2 bg-[#25d1f4] rounded-full shadow-[0_0_10px_#25d1f4]" />
                                                        </div>
                                                        <span className={cn(
                                                            "text-xs font-black tabular-nums tracking-widest transition-colors",
                                                            errors.mesafe_km ? "text-rose-500" : "text-[#25d1f4]"
                                                        )}>
                                                            {String(watch('mesafe_km'))} KM
                                                        </span>
                                                        {errors.mesafe_km && (
                                                            <p className="absolute -bottom-6 text-[10px] text-rose-500 font-bold whitespace-nowrap">
                                                                Mesafe geçersiz!
                                                            </p>
                                                        )}
                                                    </div>
                                                    <div className="flex flex-col items-end">
                                                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Varış Noktası</span>
                                                        <span className="font-black text-white text-sm">{watch('varis_yeri')}</span>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="text-center py-10 text-slate-500 text-xs font-bold uppercase tracking-[0.2em] border-2 border-dashed border-[#23353b] rounded-2xl bg-[#0a0f12]">Henüz güzergah belirlenmedi</div>
                                            )}
                                        </div>

                                        <div className="bg-[#131c20] p-6 rounded-[24px] border border-[#23353b] space-y-5">
                                            <h4 className="text-xs font-black text-emerald-400 uppercase tracking-widest flex items-center gap-2">
                                                <Weight className="w-4 h-4" /> Yük Yönetimi
                                            </h4>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="space-y-1.5">
                                                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Boş Kantar (KG)</label>
                                                    <Input type="number" placeholder="0" {...register('bos_agirlik_kg')} className="bg-[#0a0f12] border-[#23353b] focus:border-emerald-500 text-white font-black h-12 text-lg" />
                                                </div>
                                                <div className="space-y-1.5">
                                                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Dolu Kantar (KG)</label>
                                                    <Input type="number" placeholder="0" {...register('dolu_agirlik_kg')} className="bg-[#0a0f12] border-[#23353b] focus:border-emerald-500 text-white font-black h-12 text-lg" />
                                                </div>
                                            </div>
                                            <div className="pt-5 border-t border-[#23353b] flex justify-between items-center bg-[#0a0f12] -mx-6 mb-[-24px] p-6 rounded-b-[24px]">
                                                <span className="text-xs font-black text-slate-400 uppercase tracking-wider">Net Taşıma Yükü:</span>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-3xl font-black text-emerald-400 tabular-nums tracking-tighter shadow-emerald-500/10 drop-shadow-lg">{Number(watch('net_kg') || 0).toLocaleString()}</span>
                                                    <span className="text-xs font-black text-emerald-500/50 uppercase tracking-widest mt-1">KG</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {returnType !== 'none' && (
                                    <motion.div 
                                        initial={prefersReducedMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={transitionProps}
                                        className="p-6 rounded-[24px] border bg-[#1a1c13] border-amber-500/30 space-y-4"
                                    >
                                        <h4 className="text-xs font-black uppercase tracking-widest text-amber-500 flex items-center gap-2">
                                            <ArrowLeftRight className="w-4 h-4" /> Bağlı Dönüş Seferi (Otomatik)
                                        </h4>
                                        <div className="grid grid-cols-2 gap-6">
                                            <div className="space-y-1.5">
                                                <label className="text-[10px] font-bold text-amber-500/70 uppercase tracking-widest">Dönüş Seferi ID/No</label>
                                                <Input placeholder="Sistem Atayacak" {...register('return_sefer_no')} className="bg-[#0a0f12] border-amber-500/20 text-white h-12" />
                                            </div>
                                            <div className="space-y-1.5">
                                                <label className="text-[10px] font-bold text-amber-500/70 uppercase tracking-widest">Dönüş Kantar Yükü (KG)</label>
                                                <Input type="number" placeholder="0" {...register('return_net_kg')} className="bg-[#0a0f12] border-amber-500/20 text-white font-black h-12 text-lg" />
                                            </div>
                                        </div>
                                    </motion.div>
                                )}

                                <div className="space-y-2 bg-[#131c20] p-6 rounded-[24px] border border-[#23353b]">
                                    <label className="text-xs font-black text-slate-300 uppercase tracking-widest flex items-center gap-2 mb-3">Statü</label>
                                    <select {...register('durum')} className="w-full h-14 rounded-xl border border-[#23353b] bg-[#0a0f12] px-4 text-sm font-bold text-white transition-all focus:border-[#25d1f4] outline-none appearance-none cursor-pointer">
                                        <option value="Bekliyor" className="bg-[#0a0f12]">Bekliyor</option>
                                        <option value="Planlandı" className="bg-[#0a0f12]">Planlandı (İş Emri Verildi)</option>
                                        <option value="Yolda" className="bg-[#0a0f12]">Yolda</option>
                                        <option value="Devam Ediyor" className="bg-[#0a0f12]">Devam Ediyor</option>
                                        <option value="Tamam" className="bg-[#0a0f12]">Tamamlandı</option>
                                        <option value="İptal" className="bg-[#0a0f12]">İptal Edildi</option>
                                    </select>
                                </div>
                            </fieldset>
                        </motion.div>
                    ) : (
                        <motion.div 
                            key="timeline"
                            initial={prefersReducedMotion ? { opacity: 1 } : { opacity: 0, x: 10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={prefersReducedMotion ? { opacity: 1 } : { opacity: 0, x: -10 }}
                            transition={transitionProps}
                            className="min-h-[400px] overflow-y-auto max-h-[60vh] pr-2 custom-scrollbar"
                        >
                            <TripTimeline items={timeline} isLoading={isTimelineLoading} />
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="flex items-center justify-between pt-6 mt-8 border-t border-[#23353b] relative z-10">
                    <Button type="button" variant="outline" onClick={onClose} className="rounded-xl border-[#23353b] bg-[#0a0f12] text-slate-300 hover:text-white hover:bg-[#131c20] uppercase text-xs font-black tracking-widest h-14 px-6">{isReadOnly ? 'Kapat' : 'İptal Et'}</Button>
                    {activeTab === 'details' && !isReadOnly && (
                        <div className="flex gap-3">
                            <Button 
                                type="submit" 
                                variant="glossy-cyan" 
                                isLoading={isSubmitting} 
                                className="h-14 px-12 rounded-xl uppercase text-xs font-black tracking-widest shadow-[0_4px_20px_rgba(37,209,244,0.4)] hover:shadow-[0_4px_30px_rgba(37,209,244,0.6)]"
                            >
                                {isSubmitting ? 'İŞLENİYOR...' : (initialData ? 'DEĞİŞİKLİKLERİ KAYDET' : 'SEFERİ ONAYLA')}
                            </Button>
                        </div>
                    )}
                </div>
                </div>
            </form>
        </Modal>
    );
};
