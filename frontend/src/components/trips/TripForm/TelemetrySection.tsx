import React from 'react';
import { FieldErrors } from 'react-hook-form';
import { Navigation } from 'lucide-react';
import { cn } from '../../../lib/utils';
import { WeatherAnalysisCard } from '../../weather/WeatherAnalysisCard';
import { TripFormData } from '../../../types';

interface TelemetrySectionProps {
    watchedGuzergahId: number | string;
    watchedCikis: string;
    watchedVaris: string;
    watchedMesafe: number;
    weatherImpact: number | null;
    weatherLoading: boolean;
    errors: FieldErrors<TripFormData>;
}

export const TelemetrySection: React.FC<TelemetrySectionProps> = React.memo(({
    watchedGuzergahId,
    watchedCikis,
    watchedVaris,
    watchedMesafe,
    weatherImpact,
    weatherLoading,
    errors
}) => {
    return (
        <div className="bg-surface p-6 rounded-[24px] border border-border space-y-4">
            <h4 className="text-xs font-black text-secondary uppercase tracking-widest flex items-center gap-2">
                <Navigation className="w-4 h-4 text-accent" /> Telemetri Özeti
            </h4>
            <WeatherAnalysisCard weatherImpact={weatherImpact} weatherLoading={weatherLoading} />
            {watchedGuzergahId ? (
                <div className="flex items-center justify-between p-5 bg-base rounded-2xl border border-border">
                    <div className="flex flex-col">
                        <span className="text-[10px] text-secondary font-bold uppercase tracking-wider mb-1">Çıkış Noktası</span>
                        <span className="font-black text-primary text-sm">{watchedCikis}</span>
                    </div>
                    <div className="flex flex-col items-center px-4 w-full">
                        <div className="w-full h-1 bg-border rounded-full relative mb-1.5 flex justify-center items-center">
                            <div className="absolute inset-x-8 h-full bg-accent/30 rounded-full" />
                            <div className="absolute h-2 w-2 bg-accent rounded-full shadow-[0_0_10px_var(--accent)]" />
                        </div>
                        <span className={cn(
                            "text-xs font-black tabular-nums tracking-widest transition-colors",
                            errors.mesafe_km ? "text-danger" : "text-accent"
                        )}>
                            {watchedMesafe} KM
                        </span>
                        {errors.mesafe_km && (
                            <p className="absolute -bottom-6 text-[10px] text-danger font-bold whitespace-nowrap">
                                Mesafe geçersiz!
                            </p>
                        )}
                    </div>
                    <div className="flex flex-col items-end">
                        <span className="text-[10px] text-secondary font-bold uppercase tracking-wider mb-1">Varış Noktası</span>
                        <span className="font-black text-primary text-sm">{watchedVaris}</span>
                    </div>
                </div>
            ) : (
                <div className="text-center py-10 text-secondary text-xs font-bold uppercase tracking-[0.2em] border-2 border-dashed border-border rounded-2xl bg-base">
                    Henüz güzergah belirlenmedi
                </div>
            )}
        </div>
    );
});
