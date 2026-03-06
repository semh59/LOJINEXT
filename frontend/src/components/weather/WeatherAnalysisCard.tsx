import React from 'react';
import { CloudRain, Wind, Sun } from 'lucide-react';
import { cn } from '../../lib/utils';

interface WeatherAnalysisCardProps {
    weatherImpact: number | null;
    weatherLoading: boolean;
}

export const WeatherAnalysisCard: React.FC<WeatherAnalysisCardProps> = ({ weatherImpact, weatherLoading }) => {
    if (weatherImpact === null && !weatherLoading) return null;

    const getWeatherDescription = (factor: number) => {
        if (factor > 1.1) return { text: 'Yüksek Tüketim Riski', color: 'text-red-500', icon: CloudRain };
        if (factor > 1.02) return { text: 'Hafif Artış', color: 'text-orange-500', icon: Wind };
        if (factor < 0.98) return { text: 'Optimal Tasarruf', color: 'text-emerald-500', icon: Sun };
        return { text: 'Normal Koşullar', color: 'text-blue-500', icon: Sun };
    };

    const info = weatherImpact ? getWeatherDescription(weatherImpact) : { text: '', color: '', icon: Sun };

    return (
        <div className={cn("p-4 rounded-2xl border flex items-center justify-between transition-all", 
            weatherLoading ? "bg-neutral-50 border-neutral-100" : 
            (weatherImpact || 0) > 1.02 ? "bg-orange-50 border-orange-100" : "bg-emerald-50 border-emerald-100"
        )}>
            <div className="flex items-center gap-3">
                <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center transition-all", 
                    weatherLoading ? "bg-neutral-200 animate-pulse" : 
                    (weatherImpact || 0) > 1.02 ? "bg-orange-500 text-white" : "bg-emerald-500 text-white"
                )}>
                    {weatherLoading ? <Wind className="w-5 h-5 text-neutral-400" /> : <info.icon className="w-5 h-5" />}
                </div>
                <div>
                    <div className="text-[10px] font-black uppercase text-neutral-400">Hava Analizi</div>
                    <div className={cn("text-sm font-bold uppercase", weatherLoading ? "text-neutral-400" : "text-neutral-900")}>
                        {weatherLoading ? 'Hesaplanıyor...' : info.text}
                    </div>
                </div>
            </div>
            {!weatherLoading && weatherImpact !== null && (
                <div className="text-right">
                    <div className="text-[10px] font-black uppercase text-neutral-400">Etki</div>
                    <div className={cn("text-lg font-black", weatherImpact > 1.02 ? "text-orange-600" : "text-emerald-600")}>
                        {weatherImpact > 1 ? '+' : ''}{((weatherImpact - 1) * 100).toFixed(1)}%
                    </div>
                </div>
            )}
        </div>
    );
};
