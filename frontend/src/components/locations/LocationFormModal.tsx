import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Location, LocationCreate } from '../../types/location';
import { cn } from '../../lib/utils';
import { Info, MapIcon } from 'lucide-react';

const locationSchema = z.object({
    cikis_yeri: z.string().min(2, 'Çıkış yeri en az 2 karakter olmalıdır').max(100),
    varis_yeri: z.string().min(2, 'Varış yeri en az 2 karakter olmalıdır').max(100),
    mesafe_km: z.number().positive('Mesafe 0\'dan büyük olmalıdır'),
    tahmini_sure_saat: z.number().min(0).max(48),
    zorluk: z.enum(['Normal', 'Orta', 'Zor']),
    ascent_m: z.number().min(0).max(10000),
    descent_m: z.number().min(0).max(10000),
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
    notlar: string;
}

interface LocationFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (data: LocationCreate) => Promise<void>;
    location: Location | null;
}

export const LocationFormModal = ({ isOpen, onClose, onSave, location }: LocationFormModalProps) => {
    const {
        register,
        handleSubmit,
        reset,
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
                notlar: location.notlar || ''
            });
        } else {
            reset({
                cikis_yeri: '',
                varis_yeri: '',
                mesafe_km: 0,
                tahmini_sure_saat: 0,
                zorluk: 'Normal',
                ascent_m: 0,
                descent_m: 0,
                notlar: ''
            });
        }
    }, [location, reset, isOpen]);

    const onSubmit = (values: LocationFormValues) => {
        onSave(values as LocationCreate);
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
                                    step="0.1"
                                    {...register('mesafe_km', { valueAsNumber: true })}
                                    error={!!errors.mesafe_km}
                                />
                                {errors.mesafe_km && <p className="text-[10px] text-red-500 font-bold px-1">{errors.mesafe_km.message}</p>}
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Tahmini Süre (saat)</label>
                                <Input
                                    type="number"
                                    step="0.1"
                                    {...register('tahmini_sure_saat', { valueAsNumber: true })}
                                    error={!!errors.tahmini_sure_saat}
                                />
                                {errors.tahmini_sure_saat && <p className="text-[10px] text-red-500 font-bold px-1">{errors.tahmini_sure_saat.message}</p>}
                            </div>
                        </div>
                    </div>

                    {/* Teknik Detaylar */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 mb-2">
                            <Info className="w-5 h-5 text-primary" />
                            <h3 className="font-black text-neutral-900 uppercase tracking-widest text-sm">Teknik Detaylar</h3>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Zorluk Derecesi</label>
                            <select
                                {...register('zorluk')}
                                className={cn(
                                    "flex h-10 w-full rounded-xl border border-neutral-200 bg-white px-3 py-2 text-sm ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
                                    errors.zorluk && "border-red-500"
                                )}
                            >
                                <option value="Normal">Normal (Düz)</option>
                                <option value="Orta">Orta (Eğimli)</option>
                                <option value="Zor">Zor (Dağlık)</option>
                            </select>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Tırmanış (m)</label>
                                <Input
                                    type="number"
                                    {...register('ascent_m', { valueAsNumber: true })}
                                />
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">İniş (m)</label>
                                <Input
                                    type="number"
                                    {...register('descent_m', { valueAsNumber: true })}
                                />
                            </div>
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
                    <Button type="submit" isLoading={isSubmitting}>
                        {location ? 'Güncelle' : 'Kaydet'}
                    </Button>
                </div>
            </form>
        </Modal>
    );
};
