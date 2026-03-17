import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Route,
    History
} from 'lucide-react';

/**
 * Zod Şeması
 */
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Trip, Guzergah, SeferTimelineItem, Vehicle, Driver, Dorse, TripFormData } from '../../types';
import { vehiclesApi, driversApi, locationService, weatherApi } from '../../services/api';
import { dorseService } from '../../services/dorseService';
import { useQuery } from '@tanstack/react-query';
import { cn } from '../../lib/utils';
import { TripTimeline } from './TripTimeline';
import { tripService } from '../../services/api/trip-service';
import { RouteSelector } from './TripForm/RouteSelector';
import { StaffVehicleSection } from './TripForm/StaffVehicleSection';
import { LoadManagementSection } from './TripForm/LoadManagementSection';
import { DateTimeSection } from './TripForm/DateTimeSection';
import { RoundTripSelector } from './TripForm/RoundTripSelector';
import { RoundTripSection } from './TripForm/RoundTripSection';
import { TelemetrySection } from './TripForm/TelemetrySection';

/**
 * Zod Şeması
 */
export const tripSchema = z.object({
    tarih: z.string().min(1, 'Tarih gereklidir'),
    saat: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/, 'Geçersiz saat formatı (HH:mm)'),
    sefer_no: z.string().max(50, 'Max 50 karakter').optional().or(z.literal('')),

    arac_id: z.coerce.number().int().min(1, 'Araç seçimi gereklidir'),
    dorse_id: z.coerce.number().int().optional().or(z.literal(0)).nullable(),
    sofor_id: z.coerce.number().int().min(1, 'Şoför seçimi gereklidir'),
    guzergah_id: z.coerce.number().int().min(1, 'Guzergah secimi gereklidir'),
    
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
    const [timeline, setTimeline] = useState<SeferTimelineItem[]>([]);
    const [isTimelineLoading, setIsTimelineLoading] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
        watch,
        setValue,
        reset
    } = useForm<TripFormData>({
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
            reset(initialData as unknown as TripFormData);
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
    const routes = (routeData?.items as Guzergah[]) || [];

    const { data: vehicleData } = useQuery({
        queryKey: ['vehicles', 'active'],
        queryFn: () => vehiclesApi.getAll({ aktif_only: true })
    });
    const vehicles = (vehicleData?.items as Vehicle[]) || [];

    const { data: driverData } = useQuery({
        queryKey: ['drivers', 'active'],
        queryFn: () => driversApi.getAll({ aktif_only: true })
    });
    const drivers = (driverData?.items as Driver[]) || [];

    const { data: trailerData } = useQuery({
        queryKey: ['trailers', 'active'],
        queryFn: () => dorseService.getAll({ aktif_only: true })
    });
    const trailers = (trailerData as Dorse[]) || [];

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
                    const isAracActive = vehicles?.some(v => v.id === selectedRoute.varsayilan_arac_id);
                    if (isAracActive) {
                        setValue('arac_id', selectedRoute.varsayilan_arac_id);
                    }
                }
                if (selectedRoute.varsayilan_sofor_id) {
                    const isSoforActive = drivers?.some(d => d.id === selectedRoute.varsayilan_sofor_id);
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
                    sefer_no: initialData.sefer_no || '',
                    arac_id: initialData.arac_id || 0,
                    dorse_id: initialData.dorse_id || 0,
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
                    is_round_trip: initialData.is_round_trip || false,
                    return_net_kg: initialData.return_net_kg || 0,
                    return_sefer_no: initialData.return_sefer_no || ''
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
                        onSubmit(data);
                    },
                    (errors) => {
                        console.error('❌ [FORM ERROR] Validasyon hataları:', errors);
                        const fieldKeys = Object.keys(errors);
                        const errorMsg = fieldKeys.map(key => `${key}: ${(errors as any)[key]?.message}`).join(', ');
                        toast.error(`Eksik veya hatalı bilgi: ${fieldKeys.length} alan. (${fieldKeys.join(', ')})`, {
                            duration: 5000,
                            description: errorMsg
                        });
                    }
                )} 
                className="space-y-6 relative"
            >
                {initialData && (
                    <div className="flex p-1.5 bg-surface border border-border rounded-2xl mb-6 relative z-20 shadow-lg">
                        <button
                            type="button"
                            onClick={() => setActiveTab('details')}
                            className={cn(
                                "flex-1 flex items-center justify-center gap-2 py-3.5 text-xs font-black uppercase tracking-[0.1em] rounded-xl transition-all duration-200",
                                activeTab === 'details' 
                                    ? "bg-accent text-bg-base shadow-lg shadow-accent/20" 
                                    : "text-secondary hover:text-primary hover:bg-bg-elevated"
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
                                    ? "bg-accent text-bg-base shadow-lg shadow-accent/20" 
                                    : "text-secondary hover:text-primary hover:bg-bg-elevated"
                            )}
                        >
                            <History className="w-4 h-4" />
                            OPERASYON KAYDI
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
                                <RouteSelector 
                                    register={register} 
                                    errors={errors} 
                                    routes={routes} 
                                    watchedGuzergahId={watchedGuzergahId} 
                                    isReadOnly={isReadOnly} 
                                />

                                <RoundTripSelector 
                                    returnType={returnType} 
                                    setReturnType={setReturnType} 
                                    isReadOnly={isReadOnly} 
                                />

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-6">
                                        <DateTimeSection 
                                            register={register} 
                                            errors={errors} 
                                            isReadOnly={isReadOnly} 
                                        />

                                        <StaffVehicleSection 
                                            register={register} 
                                            errors={errors} 
                                            vehicles={vehicles} 
                                            drivers={drivers} 
                                            trailers={trailers} 
                                            isReadOnly={isReadOnly} 
                                        />
                                    </div>

                                    <div className="space-y-6">
                                        <TelemetrySection 
                                            watchedGuzergahId={watchedGuzergahId} 
                                            watchedCikis={watchedCikis} 
                                            watchedVaris={watchedVaris} 
                                            watchedMesafe={watch('mesafe_km')} 
                                            weatherImpact={weatherImpact} 
                                            weatherLoading={weatherLoading} 
                                            errors={errors} 
                                        />

                                        <LoadManagementSection 
                                            register={register} 
                                            errors={errors} 
                                            watchedNetKg={watch('net_kg')} 
                                            isReadOnly={isReadOnly} 
                                        />
                                    </div>
                                </div>

                                {returnType !== 'none' && (
                                    <RoundTripSection 
                                        register={register} 
                                        prefersReducedMotion={prefersReducedMotion} 
                                        transitionProps={transitionProps} 
                                    />
                                )}

                                <div className="space-y-2 bg-surface p-6 rounded-[24px] border border-border">
                                    <label className="text-xs font-black text-secondary uppercase tracking-widest flex items-center gap-2 mb-3">Statü</label>
                                    <select {...register('durum')} className="w-full h-14 rounded-xl border border-border bg-base px-4 text-sm font-bold text-primary transition-all focus:border-accent outline-none appearance-none cursor-pointer">
                                        <option value="Bekliyor" className="bg-base">Bekliyor</option>
                                        <option value="Planlandı" className="bg-base">Planlandı (İş Emri Verildi)</option>
                                        <option value="Yolda" className="bg-base">Yolda</option>
                                        <option value="Devam Ediyor" className="bg-base">Devam Ediyor</option>
                                        <option value="Tamam" className="bg-base">Tamamlandı</option>
                                        <option value="İptal" className="bg-base">İptal Edildi</option>
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

                <div className="flex items-center justify-between pt-6 mt-8 border-t border-border relative z-10">
                    <Button type="button" variant="outline" onClick={onClose} className="rounded-xl border-border bg-base text-secondary hover:text-primary hover:bg-surface uppercase text-xs font-black tracking-widest h-14 px-6">{isReadOnly ? 'Kapat' : 'İptal Et'}</Button>
                    {activeTab === 'details' && !isReadOnly && (
                        <div className="flex gap-3">
                            <Button 
                                type="submit" 
                                variant="primary" 
                                isLoading={isSubmitting} 
                                className="h-14 px-12 rounded-xl uppercase text-xs font-black tracking-widest shadow-lg"
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
