import React from 'react';
import { UseFormRegister, FieldErrors } from 'react-hook-form';
import { Weight } from 'lucide-react';
import { Input } from '../../ui/Input';

import { TripFormData } from '../../../types';

interface LoadManagementSectionProps {
    register: UseFormRegister<TripFormData>;
    errors: FieldErrors<TripFormData>;
    watchedNetKg: number;
    isReadOnly?: boolean;
}

export const LoadManagementSection: React.FC<LoadManagementSectionProps> = React.memo(({
    register,
    errors,
    watchedNetKg,
    isReadOnly = false
}) => {
    return (
        <div className="bg-surface p-6 rounded-[24px] border border-border space-y-5">
            <h4 className="text-xs font-black text-success uppercase tracking-widest flex items-center gap-2">
                <Weight className="w-4 h-4" /> Yük Yönetimi
            </h4>
            <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-secondary uppercase tracking-widest">Boş Kantar (KG)</label>
                    <Input 
                        type="number" 
                        placeholder="0" 
                        {...register('bos_agirlik_kg')} 
                        disabled={isReadOnly}
                        error={!!errors.bos_agirlik_kg}
                        className="bg-base border-border focus:border-success text-primary font-black h-12 text-lg" 
                    />
                </div>
                <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-secondary uppercase tracking-widest">Dolu Kantar (KG)</label>
                    <Input 
                        type="number" 
                        placeholder="0" 
                        {...register('dolu_agirlik_kg')} 
                        disabled={isReadOnly}
                        error={!!errors.dolu_agirlik_kg}
                        className="bg-base border-border focus:border-success text-primary font-black h-12 text-lg" 
                    />
                </div>
            </div>
            <div className="pt-5 border-t border-border flex justify-between items-center bg-base -mx-6 mb-[-24px] p-6 rounded-b-[24px]">
                <span className="text-xs font-black text-secondary uppercase tracking-wider">Net Taşıma Yükü:</span>
                <div className="flex items-center gap-2">
                    <span className="text-3xl font-black text-success tabular-nums tracking-tighter drop-shadow-lg">
                        {Math.max(0, watchedNetKg).toLocaleString()}
                    </span>
                    <span className="text-xs font-black text-success/50 uppercase tracking-widest mt-1">KG</span>
                </div>
            </div>
        </div>
    );
});
