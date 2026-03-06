import React from 'react';
import { 
    Tooltip, 
    ResponsiveContainer,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid
} from 'recharts';
import { TrendingUp, CheckCircle2, AlertTriangle, XCircle, Info, Activity } from 'lucide-react';
import { PredictionComparisonResponse } from '../../types';
import { motion } from 'framer-motion';

interface ComparisonWidgetProps {
    data: PredictionComparisonResponse;
    isLoading?: boolean;
}

export const ComparisonWidget: React.FC<ComparisonWidgetProps> = ({ data, isLoading }) => {
    if (isLoading) {
        return <div className="h-[400px] w-full animate-pulse bg-black/40 backdrop-blur-md rounded-[32px] border border-white/5" />;
    }

    if (!data || data.total_compared === 0) {
        return (
            <div className="glass-card p-8 flex flex-col items-center justify-center text-center border border-white/5 min-h-[300px]">
                <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mb-4 border border-white/10 shadow-[0_0_30px_rgba(255,255,255,0.02)]">
                    <Activity className="w-8 h-8 text-slate-500" />
                </div>
                <h3 className="text-lg font-black text-white uppercase tracking-widest">Yetersiz Veri</h3>
                <p className="text-slate-500 text-sm mt-2 max-w-[280px] leading-relaxed">
                    Karşılaştırma için hem tahmin hem gerçek tüketim verisi olan en az 1 sefer gereklidir.
                </p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 1. MAE & Summary Card */}
            <div className="lg:col-span-1 space-y-6">
                <div className="glass-card p-6 border border-[#22d3ee]/20 relative overflow-hidden group hover:border-[#22d3ee]/40 transition-colors shadow-[0_0_50px_rgba(34,211,238,0.02)]">
                    <div className="absolute top-0 right-0 p-8 opacity-[0.05] group-hover:opacity-[0.1] transition-opacity">
                        <TrendingUp className="w-24 h-24 text-[#22d3ee]" />
                    </div>
                    
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 bg-[#22d3ee]/10 rounded-xl flex items-center justify-center border border-[#22d3ee]/20 shadow-[0_0_15px_rgba(34,211,238,0.2)]">
                            <Activity className="w-5 h-5 text-[#22d3ee]" />
                        </div>
                        <div>
                            <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest leading-none">Ortalama Hata</h3>
                            <p className="text-lg font-black text-white mt-1">Model Performansı</p>
                        </div>
                    </div>

                    <div className="space-y-4 relative z-10">
                        <div className="flex items-baseline gap-2">
                            <span className="text-4xl font-black text-[#22d3ee] tracking-tighter tabular-nums drop-shadow-[0_0_10px_rgba(34,211,238,0.5)]">
                                {data.mae.toFixed(2)}
                            </span>
                            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">L/100km (MAE)</span>
                        </div>
                        
                        <div className="w-full h-2 bg-black/60 rounded-full overflow-hidden border border-white/5 shadow-inner">
                            <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: `${Math.max(10, 100 - (data.mae * 10))}%` }}
                                className="h-full bg-gradient-to-r from-[#22d3ee] to-[#d006f9] rounded-full shadow-[0_0_15px_rgba(34,211,238,0.5)]"
                            />
                        </div>
                        <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
                            <Info className="w-3.5 h-3.5 text-[#22d3ee]" />
                            RMSE Değeri: <span className="text-[#22d3ee]">{data.rmse.toFixed(2)} L/100km</span>
                        </p>
                    </div>
                </div>

                <div className="glass-card p-6 border border-white/5 relative overflow-hidden">
                    <h3 className="text-xs font-black text-white/40 uppercase tracking-widest mb-4">Doğruluk Dağılımı</h3>
                    
                    <div className="space-y-4">
                        {/* Good */}
                        <div className="space-y-1.5">
                            <div className="flex justify-between text-[11px] font-black uppercase">
                                <span className="text-emerald-400 flex items-center gap-1.5 drop-shadow-[0_0_5px_rgba(16,185,129,0.5)]">
                                    <CheckCircle2 className="w-3 h-3" /> %5 Altı (İyi)
                                </span>
                                <span className="text-white">{data.accuracy_distribution.good} Sefer</span>
                            </div>
                            <div className="w-full h-1.5 bg-black/60 rounded-full overflow-hidden border border-white/5">
                                <div className="h-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.8)]" style={{ width: `${data.accuracy_distribution.good_pct}%` }} />
                            </div>
                        </div>

                        {/* Warning */}
                        <div className="space-y-1.5">
                            <div className="flex justify-between text-[11px] font-black uppercase">
                                <span className="text-amber-400 flex items-center gap-1.5 drop-shadow-[0_0_5px_rgba(251,191,36,0.5)]">
                                    <AlertTriangle className="w-3 h-3" /> %5-%15 (Kabul)
                                </span>
                                <span className="text-white">{data.accuracy_distribution.warning} Sefer</span>
                            </div>
                            <div className="w-full h-1.5 bg-black/60 rounded-full overflow-hidden border border-white/5">
                                <div className="h-full bg-amber-500 shadow-[0_0_10px_rgba(251,191,36,0.8)]" style={{ width: `${data.accuracy_distribution.warning_pct}%` }} />
                            </div>
                        </div>

                        {/* Error */}
                        <div className="space-y-1.5">
                            <div className="flex justify-between text-[11px] font-black uppercase">
                                <span className="text-rose-400 flex items-center gap-1.5 drop-shadow-[0_0_5px_rgba(244,63,94,0.5)]">
                                    <XCircle className="w-3 h-3" /> %15 Üstü (Sapma)
                                </span>
                                <span className="text-white">{data.accuracy_distribution.error} Sefer</span>
                            </div>
                            <div className="w-full h-1.5 bg-black/60 rounded-full overflow-hidden border border-white/5">
                                <div className="h-full bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.8)]" style={{ width: `${data.accuracy_distribution.error_pct}%` }} />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* 2. Trend Line Chart */}
            <div className="lg:col-span-2 glass-card p-6 border border-white/5 flex flex-col">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest leading-none">Tahmin Analizi</h3>
                        <p className="text-lg font-black text-white mt-1">Tahmin vs Gerçek Trend</p>
                    </div>
                    <div className="flex gap-4">
                        <div className="flex items-center gap-1.5 bg-[#d006f9]/10 px-3 py-1.5 rounded-full border border-[#d006f9]/20">
                            <div className="w-2 h-2 rounded-full bg-[#d006f9] shadow-[0_0_10px_rgba(208,6,249,0.8)] animate-pulse" />
                            <span className="text-[10px] font-black uppercase text-[#d006f9] tracking-widest">Tahmin</span>
                        </div>
                        <div className="flex items-center gap-1.5 bg-[#0df259]/10 px-3 py-1.5 rounded-full border border-[#0df259]/20">
                            <div className="w-2 h-2 rounded-full bg-[#0df259] shadow-[0_0_10px_rgba(13,242,89,0.8)]" />
                            <span className="text-[10px] font-black uppercase text-[#0df259] tracking-widest">Gerçek</span>
                        </div>
                    </div>
                </div>

                <div className="h-[280px] w-full flex-1">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data.trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#0df259" stopOpacity={0.2}/>
                                    <stop offset="95%" stopColor="#0df259" stopOpacity={0}/>
                                </linearGradient>
                                <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#d006f9" stopOpacity={0.2}/>
                                    <stop offset="95%" stopColor="#d006f9" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                            <XAxis 
                                dataKey="date" 
                                axisLine={false}
                                tickLine={false}
                                tick={{ fontSize: 10, fontWeight: 700, fill: 'rgba(255,255,255,0.4)' }}
                                tickFormatter={(val) => new Date(val).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}
                            />
                            <YAxis 
                                axisLine={false}
                                tickLine={false}
                                tick={{ fontSize: 10, fontWeight: 700, fill: 'rgba(255,255,255,0.4)' }}
                            />
                            <Tooltip 
                                contentStyle={{ 
                                    backgroundColor: 'rgba(5, 11, 14, 0.9)',
                                    backdropFilter: 'blur(20px)',
                                    borderRadius: '20px', 
                                    border: '1px solid rgba(255,255,255,0.1)', 
                                    boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
                                    padding: '16px'
                                }}
                                itemStyle={{ color: '#fff', fontSize: '12px', fontWeight: 900 }}
                                labelStyle={{ fontSize: '10px', fontWeight: 800, color: 'rgba(255,255,255,0.4)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}
                            />
                            <Area 
                                type="monotone" 
                                dataKey="predicted" 
                                name="Tahmin"
                                stroke="#d006f9" 
                                strokeWidth={3}
                                fillOpacity={1} 
                                fill="url(#colorPredicted)" 
                            />
                            <Area 
                                type="monotone" 
                                dataKey="actual" 
                                name="Gerçek"
                                stroke="#0df259" 
                                strokeWidth={3}
                                fillOpacity={1} 
                                fill="url(#colorActual)" 
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                <div className="mt-6 p-4 bg-white/5 rounded-2xl flex items-center gap-3 border border-white/5">
                    <Info className="w-5 h-5 text-slate-500 shrink-0" />
                    <p className="text-[10px] font-bold text-slate-500 leading-relaxed uppercase tracking-tight">
                        Bu grafik son <span className="text-white">{data.total_compared}</span> seferden alınan verilerle oluşturulmuştur. 
                        MAE (Hata) değeri sıfıra yaklaştıkça model doğruluğu artar.
                    </p>
                </div>
            </div>
        </div>
    );
};
