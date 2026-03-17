import React from 'react';
import { UseFormRegister, FieldErrors } from 'react-hook-form';
import { Clock } from 'lucide-react';
import { Input } from '../../ui/Input';

import { TripFormData } from '../../../types';

interface DateTimeSectionProps {
    register: UseFormRegister<TripFormData>;
    errors: FieldErrors<TripFormData>;
    isReadOnly?: boolean;
}

export const DateTimeSection: React.FC<DateTimeSectionProps> = React.memo(({
    register,
    errors,
    isReadOnly = false
}) => {
    return (
        <div className="bg-surface p-6 rounded-[24px] border border-border space-y-5">
            <h4 className="text-xs font-black text-secondary uppercase tracking-widest flex items-center gap-2">
                <Clock className="w-4 h-4 text-accent" /> Takvim ve Saat
            </h4>
            <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-secondary uppercase tracking-widest">Tarih</label>
                    <Input 
                        type="date" 
                        {...register('tarih')} 
                        disabled={isReadOnly}
                        error={!!errors.tarih} 
                        className="bg-bg-elevated/50 border-border focus:border-accent h-12 text-primary" 
                    />
                </div>
                <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-secondary uppercase tracking-widest">Saat</label>
                    <Input 
                        type="time" 
                        {...register('saat')} 
                        disabled={isReadOnly}
                        error={!!errors.saat} 
                        className="bg-base border-border focus:border-accent h-12 text-primary" 
                    />
                </div>
            </div>
            <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-secondary uppercase tracking-widest">Sefer No (HBL/İş No)</label>
                <Input 
                    placeholder="Örn: SEF-2024-001" 
                    {...register('sefer_no')} 
                    disabled={isReadOnly}
                    error={!!errors.sefer_no} 
                    autoComplete="off" 
                    className="bg-base border-border focus:border-accent h-12 text-primary" 
                />
                {errors.sefer_no && <p className="text-xs text-danger font-bold">{(errors.sefer_no as any).message}</p>}
            </div>
        </div>
    );
});
