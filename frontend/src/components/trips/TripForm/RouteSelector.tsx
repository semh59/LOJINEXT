import React, { useMemo } from 'react';
import { UseFormRegister, FieldErrors } from 'react-hook-form';
import { Route, MapPin, X } from 'lucide-react';
import { Guzergah, TripFormData } from '../../../types';
import { cn } from '../../../lib/utils';

interface RouteSelectorProps {
    register: UseFormRegister<TripFormData>;
    errors: FieldErrors<TripFormData>;
    routes: Guzergah[];
    watchedGuzergahId: number | string;
    isReadOnly?: boolean;
}

export const RouteSelector: React.FC<RouteSelectorProps> = React.memo(({
    register,
    errors,
    routes,
    watchedGuzergahId,
    isReadOnly = false
}) => {
    const selectedRoute = useMemo(() => 
        routes.find(r => r.id === Number(watchedGuzergahId)),
        [routes, watchedGuzergahId]
    );

    return (
        <div className="bg-surface p-6 rounded-[24px] border border-border shadow-lg group">
            <label className="text-xs font-black text-accent uppercase tracking-wider flex items-center gap-2 mb-4">
                <Route className="w-4 h-4" />
                Güzergah Seçimi
            </label>
            <div className="relative">
                <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-secondary z-10" />
                <select
                    {...register('guzergah_id')}
                    disabled={isReadOnly}
                    className={cn(
                        "w-full pl-12 h-14 rounded-xl border bg-base text-primary text-base font-bold transition-all outline-none appearance-none shadow-inner",
                        watchedGuzergahId && selectedRoute && !selectedRoute.aktif 
                            ? "border-danger text-danger focus:ring-2 focus:ring-danger/20" 
                            : "border-border hover:border-text-secondary/40 focus:border-accent focus:ring-2 focus:ring-accent/20"
                    )}
                >
                    <option value="" className="text-secondary">Güzergah arayın veya listeden seçin...</option>
                    {routes?.map((r: Guzergah) => (
                        <option key={r.id} value={r.id} className={!r.aktif ? "bg-danger text-bg-base" : "bg-surface text-primary"}>
                            {r.ad || `${r.cikis_yeri} - ${r.varis_yeri}`} {!r.aktif && "(Pasif)"} ({r.mesafe_km} km)
                        </option>
                    ))}
                </select>
            </div>
            {errors.guzergah_id && (
                <p className="mt-2 text-xs text-danger font-bold flex items-center gap-1">
                    <X className="w-3.5 h-3.5" /> {(errors.guzergah_id as any).message || 'Güzergah seçimi zorunludur!'}
                </p>
            )}
            {selectedRoute && !selectedRoute.aktif && (
                <p className="mt-4 text-xs font-bold text-danger flex items-center gap-2 bg-danger/10 p-3 rounded-lg border border-danger/20">
                    <X className="w-4 h-4" /> Dikkat: Seçilen güzergah sistemde pasif durumdadır.
                </p>
            )}
        </div>
    );
});
