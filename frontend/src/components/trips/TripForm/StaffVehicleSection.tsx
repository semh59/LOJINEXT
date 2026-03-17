import React from 'react';
import { UseFormRegister, FieldErrors } from 'react-hook-form';
import { Truck } from 'lucide-react';
import { Vehicle, Driver, Dorse, TripFormData } from '../../../types';
import { cn } from '../../../lib/utils';

interface StaffVehicleSectionProps {
    register: UseFormRegister<TripFormData>;
    errors: FieldErrors<TripFormData>;
    vehicles: Vehicle[];
    drivers: Driver[];
    trailers: Dorse[];
    isReadOnly?: boolean;
}

export const StaffVehicleSection: React.FC<StaffVehicleSectionProps> = React.memo(({
    register,
    errors,
    vehicles,
    drivers,
    trailers,
    isReadOnly = false
}) => {
    return (
        <div className="bg-surface p-6 rounded-[24px] border border-border space-y-5">
            <h4 className="text-xs font-black text-secondary uppercase tracking-widest flex items-center gap-2">
                <Truck className="w-4 h-4 text-accent" /> Personel & Araç Seçimi
            </h4>
            <div className="space-y-4">
                <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-secondary uppercase tracking-widest">Araç Plakası</label>
                    <select 
                        {...register('arac_id')} 
                        disabled={isReadOnly}
                        className={cn(
                            "w-full h-12 rounded-xl border bg-base px-4 text-sm font-bold transition-all outline-none appearance-none",
                            errors.arac_id ? "border-danger text-danger focus:border-danger" : "border-border text-primary focus:border-accent"
                        )}
                    >
                        <option value="0" className="text-secondary">Seçim Yapınız...</option>
                        {vehicles?.map(v => <option key={v.id} value={v.id} className="bg-base text-primary">{v.plaka}</option>)}
                    </select>
                    {errors.arac_id && <p className="text-[10px] text-danger font-bold">{(errors.arac_id as any).message}</p>}
                </div>
                <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-secondary uppercase tracking-widest">Dorse (Opsiyonel)</label>
                    <select 
                        {...register('dorse_id')} 
                        disabled={isReadOnly}
                        className="w-full h-12 rounded-xl border border-border bg-base px-4 text-sm font-bold text-primary transition-all focus:border-accent outline-none appearance-none"
                    >
                        <option value="0" className="text-secondary">Seçim Yok</option>
                        {trailers?.map(t => <option key={t.id} value={t.id} className="bg-base text-primary">{t.plaka}</option>)}
                    </select>
                </div>
                <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-secondary uppercase tracking-widest">Sürücü Müsaitliği</label>
                    <select 
                        {...register('sofor_id')} 
                        disabled={isReadOnly}
                        className={cn(
                            "w-full h-12 rounded-xl border bg-base px-4 text-sm font-bold transition-all outline-none appearance-none",
                            errors.sofor_id ? "border-danger text-danger focus:border-danger" : "border-border text-primary focus:border-accent"
                        )}
                    >
                        <option value="0" className="text-secondary">Şoför Ataması Yapınız...</option>
                        {drivers?.map(d => <option key={d.id} value={d.id} className="bg-base text-primary">{d.ad_soyad}</option>)}
                    </select>
                    {errors.sofor_id && <p className="text-[10px] text-danger font-bold">{(errors.sofor_id as any).message}</p>}
                </div>
            </div>
        </div>
    );
});
