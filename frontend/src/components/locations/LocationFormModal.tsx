import { useEffect, useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Location, LocationCreate } from '../../types/location';
import { Info, MapIcon } from 'lucide-react';
import { locationService } from '../../services/api/location-service';
import { toast } from 'sonner';

const locationSchema = z.object({
    cikis_yeri: z.string().min(2, 'Çıkış yeri en az 2 karakter olmalıdır').max(100),
    varis_yeri: z.string().min(2, 'Varış yeri en az 2 karakter olmalıdır').max(100),
    mesafe_km: z.number().positive('Mesafe 0\'dan büyük olmalıdır'),
    tahmini_sure_saat: z.number().min(0).max(48),
    zorluk: z.enum(['Normal', 'Orta', 'Zor']),
    ascent_m: z.number().min(0).max(10000),
    descent_m: z.number().min(0).max(10000),
    flat_distance_km: z.number().min(0).optional(),
    otoban_mesafe_km: z.number().min(0).optional(),
    sehir_ici_mesafe_km: z.number().min(0).optional(),
    cikis_lat: z.number().min(-90).max(90),
    cikis_lon: z.number().min(-180).max(180),
    varis_lat: z.number().min(-90).max(90),
    varis_lon: z.number().min(-180).max(180),
    notlar: z.string().max(500)
});

interface LocationFormValues {
    cikis_yeri: string;
    varis_yeri: string;
    mesafe_km: number;
    tahmini_sure_saat: number;
    zorluk: 'Normal' | 'Orta' | 'Zor';
    ascent_m: number;
    descent_m: number;
    flat_distance_km?: number;
    otoban_mesafe_km?: number;
    sehir_ici_mesafe_km?: number;
    cikis_lat: number;
    cikis_lon: number;
    varis_lat: number;
    varis_lon: number;
    notlar: string;
}

interface LocationFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (data: LocationCreate) => Promise<void>;
    location: Location | null;
}

const formatDuration = (hours: number): string => {
    if (!hours || hours <= 0) return '00:00:00';
    const totalSeconds = Math.round(hours * 3600);
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
};

export const LocationFormModal = ({ isOpen, onClose, onSave, location }: LocationFormModalProps) => {
    const {
        register,
        handleSubmit,
        reset,
        control,
        setValue,
        watch,
        formState: { errors, isSubmitting }
    } = useForm<LocationFormValues>({
        resolver: zodResolver(locationSchema),
        defaultValues: {
            cikis_yeri: '',
            varis_yeri: '',
            mesafe_km: 0,
            tahmini_sure_saat: 0,
            zorluk: 'Normal',
            ascent_m: 0,
            descent_m: 0,
            flat_distance_km: 0,
            otoban_mesafe_km: 0,
            sehir_ici_mesafe_km: 0,
            cikis_lat: undefined,
            cikis_lon: undefined,
            varis_lat: undefined,
            varis_lon: undefined,
            notlar: ''
        }
    });

    useEffect(() => {
        if (location) {
            reset({
                cikis_yeri: location.cikis_yeri,
                varis_yeri: location.varis_yeri,
                mesafe_km: location.mesafe_km,
                tahmini_sure_saat: location.tahmini_sure_saat || 0,
                zorluk: (location.zorluk as any) || 'Normal',
                ascent_m: location.ascent_m || 0,
                descent_m: location.descent_m || 0,
                flat_distance_km: location.flat_distance_km || 0,
                otoban_mesafe_km: location.otoban_mesafe_km || 0,
                sehir_ici_mesafe_km: location.sehir_ici_mesafe_km || 0,
                cikis_lat: location.cikis_lat,
                cikis_lon: location.cikis_lon,
                varis_lat: location.varis_lat,
                varis_lon: location.varis_lon,
                notlar: location.notlar || ''
            });
            setRouteAnalysisData(location.route_analysis || null);
        } else {
            reset({
                cikis_yeri: '',
                varis_yeri: '',
                mesafe_km: 0,
                tahmini_sure_saat: 0,
                zorluk: 'Normal',
                ascent_m: 0,
                descent_m: 0,
                flat_distance_km: 0,
                otoban_mesafe_km: 0,
                sehir_ici_mesafe_km: 0,
                cikis_lat: undefined,
                cikis_lon: undefined,
                varis_lat: undefined,
                varis_lon: undefined,
                notlar: ''
            });
            setRouteAnalysisData(null);
        }
    }, [location, reset, isOpen]);

    const onSubmit = async (values: LocationFormValues) => {
        try {
            // Standardize names to prevent duplicates locally
            const normalizedValues = {
                ...values,
                cikis_yeri: values.cikis_yeri.trim().split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' '),
                varis_yeri: values.varis_yeri.trim().split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
            };
            await onSave(normalizedValues as LocationCreate);
            onClose();
        } catch (error) {
            console.error('Kaydetme hatası:', error);
            toast.error('Kayıt sırasında bir hata oluştu');
        }
    };

    const [isCalculating, setIsCalculating] = useState(false);
    const [routeAnalysisData, setRouteAnalysisData] = useState<any>(null);
    const watchedSure = watch('tahmini_sure_saat');

    // Watch values for display
    const cikisLat = useWatch({ control, name: 'cikis_lat' });
    const cikisLon = useWatch({ control, name: 'cikis_lon' });
    const varisLat = useWatch({ control, name: 'varis_lat' });
    const varisLon = useWatch({ control, name: 'varis_lon' });

    const handleCalculate = async () => {
        if (!cikisLat || !cikisLon || !varisLat || !varisLon) {
             toast.error('Lütfen koordinatları tam giriniz');
             return;
        }
        
        setIsCalculating(true);
        try {
            const data = await locationService.getRouteInfo({
                cikis_lat: Number(cikisLat),
                cikis_lon: Number(cikisLon),
                varis_lat: Number(varisLat),
                varis_lon: Number(varisLon)
            });

            if (data) {
                // Map Backend Difficulty to Frontend Enum
                let mappedDifficulty: 'Normal' | 'Orta' | 'Zor' = 'Normal';
                if (data.difficulty === 'Düz') mappedDifficulty = 'Normal';
                else if (data.difficulty === 'Hafif Eğimli') mappedDifficulty = 'Orta';
                else if (data.difficulty === 'Dik/Dağlık') mappedDifficulty = 'Zor';

                setValue('mesafe_km', data.distance_km, { shouldValidate: true, shouldDirty: true });
                setValue('tahmini_sure_saat', data.duration_min / 60, { shouldValidate: true, shouldDirty: true });
                setValue('zorluk', mappedDifficulty, { shouldValidate: true, shouldDirty: true });
                
                // Update hidden & detailed fields
                setValue('ascent_m', data.ascent_m || 0);
                setValue('descent_m', data.descent_m || 0);
                setValue('flat_distance_km', data.flat_distance_km || 0);
                setValue('otoban_mesafe_km', data.otoban_mesafe_km || 0);
                setValue('sehir_ici_mesafe_km', data.sehir_ici_mesafe_km || 0);
                
                if (data.route_analysis) {
                    setRouteAnalysisData(data.route_analysis);
                }
                
                toast.success('Rota bilgileri başarıyla hesaplandı');
            }
        } catch (error) {
            console.error('Hesaplama hatası:', error);
            toast.error('Rota hesaplanırken bir hata oluştu');
        } finally {
            setIsCalculating(false);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={location ? 'Güzergahı Düzenle' : 'Yeni Güzergah Ekle'}
            size="lg"
        >
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Lokasyon Bilgileri */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 mb-2">
                            <MapIcon className="w-5 h-5 text-primary" />
                            <h3 className="font-black text-neutral-900 uppercase tracking-widest text-sm">Rota Bilgileri</h3>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Çıkış Yeri*</label>
                            <Input
                                {...register('cikis_yeri')}
                                placeholder="Örn: Ankara"
                                error={!!errors.cikis_yeri}
                            />
                            {errors.cikis_yeri && <p className="text-[10px] text-red-500 font-bold px-1">{errors.cikis_yeri.message}</p>}
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Varış Yeri*</label>
                            <Input
                                {...register('varis_yeri')}
                                placeholder="Örn: İstanbul"
                                error={!!errors.varis_yeri}
                            />
                            {errors.varis_yeri && <p className="text-[10px] text-red-500 font-bold px-1">{errors.varis_yeri.message}</p>}
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Mesafe (km)*</label>
                                <Input
                                    type="number"
                                    step="any"
                                    {...register('mesafe_km', { valueAsNumber: true })}
                                    readOnly
                                    className="bg-neutral-50 cursor-not-allowed font-black text-primary border-dashed"
                                    error={!!errors.mesafe_km}
                                />
                                {errors.mesafe_km && <p className="text-[10px] text-red-500 font-bold px-1">{errors.mesafe_km.message}</p>}
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Tahmini Süre</label>
                                <Input
                                    value={formatDuration(watchedSure)}
                                    readOnly
                                    className="bg-neutral-50 cursor-not-allowed font-black text-primary"
                                    placeholder="00:00:00"
                                />
                                <input type="hidden" {...register('tahmini_sure_saat', { valueAsNumber: true })} />
                            </div>
                        </div>
                    </div>



                    {/* Koordinat Bilgileri */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                                <MapIcon className="w-5 h-5 text-primary" />
                                <h3 className="font-black text-neutral-900 uppercase tracking-widest text-sm">Koordinat Bilgileri</h3>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Çıkış Enlem (Lat)*</label>
                                <Input
                                    type="number"
                                    step="0.000001"
                                    {...register('cikis_lat', { valueAsNumber: true })}
                                    error={!!errors.cikis_lat}
                                />
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Çıkış Boylam (Lon)*</label>
                                <Input
                                    type="number"
                                    step="0.000001"
                                    {...register('cikis_lon', { valueAsNumber: true })}
                                    error={!!errors.cikis_lon}
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Varış Enlem (Lat)*</label>
                                <Input
                                    type="number"
                                    step="0.000001"
                                    {...register('varis_lat', { valueAsNumber: true })}
                                    error={!!errors.varis_lat}
                                />
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Varış Boylam (Lon)*</label>
                                <Input
                                    type="number"
                                    step="0.000001"
                                    {...register('varis_lon', { valueAsNumber: true })}
                                    error={!!errors.varis_lon}
                                />
                            </div>
                        </div>
                        
                        <div className="space-y-3">
                            <div className="text-[10px] text-neutral-400 italic px-1">
                                * Koordinatlar girildikten sonra "Rotayı Hesapla" ile veriler otomatik doldurulur.
                            </div>
                            <Button 
                                type="button" 
                                variant="primary"
                                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold"
                                onClick={handleCalculate}
                                disabled={!cikisLat || !cikisLon || !varisLat || !varisLon || isCalculating}
                            >
                                {isCalculating ? 'Hesaplanıyor...' : 'Rotayı Hesapla'}
                            </Button>
                        </div>
                    </div>

                    {/* Teknik Detaylar */}
                    <div className="col-span-full space-y-4">
                        <div className="flex items-center gap-2 mb-2">
                            <Info className="w-5 h-5 text-primary" />
                            <h3 className="font-black text-neutral-900 uppercase tracking-widest text-sm">Teknik ve Yol Detayları</h3>
                        </div>

                        {routeAnalysisData && (
                            <div className="bg-neutral-50 p-4 rounded-xl border border-neutral-200 mb-4 animate-in fade-in slide-in-from-top-2">
                                <h4 className="font-black text-xs text-neutral-500 uppercase tracking-widest mb-3 border-b border-neutral-200 pb-2">
                                    Detaylı Yol Analizi
                                </h4>
                                <div className="grid grid-cols-2 gap-8">
                                    {/* Otoban */}
                                    <div>
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-bold text-sm bg-blue-50 text-blue-700 px-2 py-0.5 rounded">Otoban</span>
                                            <span className="font-black text-sm text-neutral-900">
                                                {((routeAnalysisData.highway?.flat || 0) + (routeAnalysisData.highway?.up || 0) + (routeAnalysisData.highway?.down || 0)).toFixed(1)} km
                                            </span>
                                        </div>
                                        <div className="space-y-1.5 text-xs">
                                            <div className="flex justify-between items-center text-neutral-600">
                                                <span>Düz:</span> 
                                                <span className="font-mono font-medium">{routeAnalysisData.highway?.flat?.toFixed(1) || 0} km</span>
                                            </div>
                                            <div className="flex justify-between items-center text-red-600">
                                                <span>Tırmanış:</span> 
                                                <span className="font-mono font-medium">{(routeAnalysisData.highway?.up || 0).toFixed(1)} km</span>
                                            </div>
                                            <div className="flex justify-between items-center text-green-600">
                                                <span>İniş:</span> 
                                                <span className="font-mono font-medium">{(routeAnalysisData.highway?.down || 0).toFixed(1)} km</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    {/* Şehiriçi */}
                                    <div>
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-bold text-sm bg-orange-50 text-orange-700 px-2 py-0.5 rounded">Şehiriçi / Diğer</span>
                                            <span className="font-black text-sm text-neutral-900">
                                                {((routeAnalysisData.other?.flat || 0) + (routeAnalysisData.other?.up || 0) + (routeAnalysisData.other?.down || 0)).toFixed(1)} km
                                            </span>
                                        </div>
                                        <div className="space-y-1.5 text-xs">
                                            <div className="flex justify-between items-center text-neutral-600">
                                                <span>Düz:</span> 
                                                <span className="font-mono font-medium">{(routeAnalysisData.other?.flat || 0).toFixed(1)} km</span>
                                            </div>
                                            <div className="flex justify-between items-center text-red-600">
                                                <span>Tırmanış:</span> 
                                                <span className="font-mono font-medium">{(routeAnalysisData.other?.up || 0).toFixed(1)} km</span>
                                            </div>
                                            <div className="flex justify-between items-center text-green-600">
                                                <span>İniş:</span> 
                                                <span className="font-mono font-medium">{(routeAnalysisData.other?.down || 0).toFixed(1)} km</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="hidden">
                            <input {...register('zorluk')} />
                            <input type="number" step="any" {...register('otoban_mesafe_km', { valueAsNumber: true })} />
                            <input type="number" step="any" {...register('sehir_ici_mesafe_km', { valueAsNumber: true })} />
                            <input type="number" step="any" {...register('flat_distance_km', { valueAsNumber: true })} />
                            <input type="number" step="any" {...register('ascent_m', { valueAsNumber: true })} />
                            <input type="number" step="any" {...register('descent_m', { valueAsNumber: true })} />
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Notlar</label>
                            <textarea
                                {...register('notlar')}
                                className="flex min-h-[80px] w-full rounded-xl border border-neutral-200 bg-white px-3 py-2 text-sm placeholder:text-neutral-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
                                placeholder="Güzergah hakkında ek bilgiler..."
                            />
                        </div>
                    </div>
                </div>

                <div className="flex justify-end gap-3 pt-6 border-t border-neutral-100">
                    <Button variant="secondary" type="button" onClick={onClose}>İptal</Button>
                    <Button type="submit" isLoading={isSubmitting} disabled={isCalculating}>
                        {location ? 'Güncelle' : 'Kaydet'}
                    </Button>
                </div>
            </form>
        </Modal>
    );
};
