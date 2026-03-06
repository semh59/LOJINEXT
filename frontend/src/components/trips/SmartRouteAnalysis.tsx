import React from 'react';
import { motion } from 'framer-motion';
import { Trip } from '../../types';
import { TrendingUp, TrendingDown, Minus, Route, MapPin } from 'lucide-react';
import { cn } from '../../lib/utils';

interface SmartRouteAnalysisProps {
    trip: Trip;
}

export const SmartRouteAnalysis: React.FC<SmartRouteAnalysisProps> = ({ trip }) => {
    // Robust parsing for rota_detay
    let analysis = trip.rota_detay?.route_analysis;
    if (typeof trip.rota_detay === 'string') {
        try {
            analysis = JSON.parse(trip.rota_detay).route_analysis;
        } catch (e) {
            console.warn('Failed to parse rota_detay json', e);
        }
    }

    if (!analysis) {
        // Fallback using flat columns if route_analysis is missing
        if (trip.otoban_mesafe_km != null) {
             const fallbackHwy = Number(trip.otoban_mesafe_km) || 0;
             const fallbackTotal = (Number(trip.mesafe_km) || 1);
             
             // Construct temporary analysis object for rendering
             analysis = { 
                highway: { flat: fallbackHwy, up: 0, down: 0 },
                other: { flat: fallbackTotal - fallbackHwy, up: 0, down: 0 },
                motorway: { flat: 0, up: 0, down: 0 }, // Dummy to prevent crash
                trunk: { flat: 0, up: 0, down: 0 },
                primary: { flat: 0, up: 0, down: 0 }
             }; 
        } else {
             return (
                <div className="p-6 bg-neutral-50/50 rounded-2xl border border-dashed border-neutral-200 text-center">
                    <span className="text-xs font-bold text-neutral-400 uppercase tracking-widest">
                        Bu sefer için detaylı yol analizi henüz mevcut değil.
                    </span>
                </div>
            );
        }
    }

    const highway = analysis.highway || { flat: 0, up: 0, down: 0 };
    const other = analysis.other || { flat: 0, up: 0, down: 0 };
    
    const totalKm = (Number(trip.mesafe_km) || 1);
    const highwayTotal = Object.values(highway).reduce((acc: number, val: any) => acc + (Number(val) || 0), 0);
    const highwayPct = Math.round((highwayTotal / totalKm) * 100);

    const steepnessData = [
        { label: 'Yokuş Yukarı', val: (analysis.motorway?.up || 0) + (analysis.trunk?.up || 0) + (analysis.primary?.up || 0) + (other.up || 0), icon: TrendingUp, color: 'text-rose-500', bg: 'bg-rose-50' },
        { label: 'Düz Yol', val: (analysis.motorway?.flat || 0) + (analysis.trunk?.flat || 0) + (analysis.primary?.flat || 0) + (other.flat || 0), icon: Minus, color: 'text-emerald-500', bg: 'bg-emerald-50' },
        { label: 'Yokuş Aşağı', val: (analysis.motorway?.down || 0) + (analysis.trunk?.down || 0) + (analysis.primary?.down || 0) + (other.down || 0), icon: TrendingDown, color: 'text-blue-500', bg: 'bg-blue-50' },
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 bg-white rounded-[32px] border border-neutral-100 shadow-sm">
            {/* Road Type Distribution */}
            <div className="space-y-4">
                <div className="flex items-center gap-2">
                    <Route className="w-5 h-5 text-indigo-500" />
                    <h4 className="text-sm font-black text-neutral-900 uppercase tracking-tight">Yol Karakteristiği</h4>
                </div>
                
                <div className="space-y-3">
                    <div className="flex justify-between items-end">
                        <span className="text-[11px] font-black text-neutral-400 uppercase tracking-widest">Otoyol / Ana Yol</span>
                        <span className="text-sm font-black text-indigo-600">%{highwayPct}</span>
                    </div>
                    <div className="h-3 w-full bg-neutral-100 rounded-full overflow-hidden">
                        <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${highwayPct}%` }}
                            className="h-full bg-gradient-to-r from-indigo-500 to-violet-500"
                        />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 mt-4">
                        <div className="p-3 bg-neutral-50 rounded-2xl border border-neutral-100">
                            <span className="block text-[10px] font-bold text-neutral-400 uppercase mb-1">Otoyol</span>
                            <span className="text-sm font-black text-neutral-900">{highwayTotal.toFixed(1)} <span className="text-[10px]">km</span></span>
                        </div>
                        <div className="p-3 bg-neutral-50 rounded-2xl border border-neutral-100">
                            <span className="block text-[10px] font-bold text-neutral-400 uppercase mb-1">Şehir İçi / Diğer</span>
                            <span className="text-sm font-black text-neutral-900">{(totalKm - highwayTotal).toFixed(1)} <span className="text-[10px]">km</span></span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Steepness / Trend */}
            <div className="space-y-4">
                <div className="flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-emerald-500" />
                    <h4 className="text-sm font-black text-neutral-900 uppercase tracking-tight">Eğim & Rakım Trendi</h4>
                </div>

                <div className="grid grid-cols-3 gap-3">
                    {steepnessData.map((item, idx) => (
                        <div key={idx} className={cn("p-4 rounded-3xl border border-neutral-100 flex flex-col items-center gap-2", item.bg)}>
                            <item.icon className={cn("w-6 h-6", item.color)} />
                            <div className="text-center">
                                <span className="block text-xs font-black text-neutral-900">{item.val.toFixed(1)} <span className="text-[9px]">km</span></span>
                                <span className="text-[9px] font-bold text-neutral-400 uppercase tracking-tighter">{item.label}</span>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="mt-2 p-4 bg-emerald-50/30 rounded-2xl border border-emerald-100/50 flex justify-between items-center">
                    <div>
                        <span className="block text-[10px] font-bold text-emerald-600 uppercase">İrtifa Kazanımı</span>
                        <span className="text-lg font-black text-emerald-700">{((trip.ascent_m || 0) / 1000).toFixed(2)} <span className="text-xs">km</span></span>
                    </div>
                    <div className="text-right">
                        <span className="block text-[10px] font-bold text-blue-600 uppercase">İrtifa Kaybı</span>
                        <span className="text-lg font-black text-blue-700">{((trip.descent_m || 0) / 1000).toFixed(2)} <span className="text-xs">km</span></span>
                    </div>
                </div>
            </div>
        </div>
    );
};
