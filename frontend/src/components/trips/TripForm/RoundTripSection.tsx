import React from 'react';
import { UseFormRegister } from 'react-hook-form';
import { motion } from 'framer-motion';
import { ArrowLeftRight } from 'lucide-react';
import { Input } from '../../ui/Input';
import { TripFormData } from '../../../types';

interface RoundTripSectionProps {
    register: UseFormRegister<TripFormData>;
    prefersReducedMotion: boolean;
    transitionProps: any;
}

export const RoundTripSection: React.FC<RoundTripSectionProps> = React.memo(({
    register,
    prefersReducedMotion,
    transitionProps
}) => {
    return (
        <motion.div 
            initial={prefersReducedMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={transitionProps}
            className="p-6 rounded-[24px] border bg-warning/5 border-warning/30 space-y-4"
        >
            <h4 className="text-xs font-black uppercase tracking-widest text-warning flex items-center gap-2">
                <ArrowLeftRight className="w-4 h-4" /> Bağlı Dönüş Seferi (Otomatik)
            </h4>
            <div className="grid grid-cols-2 gap-6">
                <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-warning/70 uppercase tracking-widest">Dönüş Seferi ID/No</label>
                    <Input placeholder="Sistem Atayacak" {...register('return_sefer_no')} className="bg-bg-elevated border-warning/20 text-primary h-12" />
                </div>
                <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-warning/70 uppercase tracking-widest">Dönüş Kantar Yükü (KG)</label>
                    <Input type="number" placeholder="0" {...register('return_net_kg')} className="bg-bg-elevated border-warning/20 text-primary font-black h-12 text-lg" />
                </div>
            </div>
        </motion.div>
    );
});
