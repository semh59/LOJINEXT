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
        return <div className="h-[400px] w-full animate-pulse bg-surface/50 rounded-2xl border border-border" />;
    }

    if (!data || data.total_compared === 0) {
        return (
            <div className="bg-surface p-8 flex flex-col items-center justify-center text-center border border-border rounded-2xl min-h-[300px] shadow-sm">
                <div className="w-16 h-16 bg-bg-elevated rounded-2xl flex items-center justify-center mb-4 border border-border">
                    <Activity className="w-8 h-8 text-secondary" />
                </div>
                <h3 className="text-lg font-bold text-primary uppercase tracking-widest">Yetersiz Veri</h3>
                <p className="text-secondary text-sm mt-2 max-w-[280px] leading-relaxed">
                    Karşılaştırma için hem tahmin hem gerçek tüketim verisi olan en az 1 sefer gereklidir.
                </p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 1. MAE & Summary Card */}
            <div className="lg:col-span-1 space-y-6">
                <div className="bg-surface p-6 border border-info/20 rounded-2xl relative overflow-hidden group hover:border-info/40 transition-colors shadow-sm">
                    <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.06] transition-opacity">
                        <TrendingUp className="w-24 h-24 text-info" />
                    </div>
                    
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 bg-info/10 rounded-xl flex items-center justify-center border border-info/20">
                            <Activity className="w-5 h-5 text-info" />
                        </div>
                        <div>
                            <h3 className="text-[10px] font-bold text-secondary uppercase tracking-widest leading-none">Ortalama Hata</h3>
                            <p className="text-lg font-bold text-primary mt-1">Model Performansı</p>
                        </div>
                    </div>

                    <div className="space-y-4 relative z-10">
                        <div className="flex items-baseline gap-2">
                            <span className="text-4xl font-bold text-info tracking-tighter tabular-nums text-shadow-sm">
                                {data.mae.toFixed(2)}
                            </span>
                            <span className="text-[10px] font-bold text-secondary uppercase tracking-widest">L/100km (MAE)</span>
                        </div>
                        
                        <div className="w-full h-2 bg-bg-elevated rounded-full overflow-hidden border border-border">
                            <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: `${Math.max(10, 100 - (data.mae * 10))}%` }}
                                className="h-full bg-info rounded-full"
                            />
                        </div>
                        <p className="text-[9px] font-bold text-secondary uppercase tracking-widest flex items-center gap-1.5">
                            <Info className="w-3.5 h-3.5 text-info" />
                            RMSE Değeri: <span className="text-info">{data.rmse.toFixed(2)} L/100km</span>
                        </p>
                    </div>
                </div>

                <div className="bg-surface p-6 border border-border rounded-2xl relative overflow-hidden shadow-sm">
                    <h3 className="text-xs font-bold text-secondary uppercase tracking-widest mb-4">Doğruluk Dağılımı</h3>
                    
                    <div className="space-y-4">
                        {/* Good */}
                        <div className="space-y-1.5">
                            <div className="flex justify-between text-[11px] font-bold uppercase transition-colors">
                                <span className="text-success flex items-center gap-1.5">
                                    <CheckCircle2 className="w-3 h-3" /> %5 Altı (İyi)
                                </span>
                                <span className="text-primary">{data.accuracy_distribution.good} Sefer</span>
                            </div>
                            <div className="w-full h-1.5 bg-bg-elevated rounded-full overflow-hidden border border-border">
                                <div className="h-full bg-success shadow-sm" style={{ width: `${data.accuracy_distribution.good_pct}%` }} />
                            </div>
                        </div>

                        {/* Warning */}
                        <div className="space-y-1.5">
                            <div className="flex justify-between text-[11px] font-bold uppercase transition-colors">
                                <span className="text-warning flex items-center gap-1.5">
                                    <AlertTriangle className="w-3 h-3" /> %5-%15 (Kabul)
                                </span>
                                <span className="text-primary">{data.accuracy_distribution.warning} Sefer</span>
                            </div>
                            <div className="w-full h-1.5 bg-bg-elevated rounded-full overflow-hidden border border-border">
                                <div className="h-full bg-warning shadow-sm" style={{ width: `${data.accuracy_distribution.warning_pct}%` }} />
                            </div>
                        </div>

                        {/* Error */}
                        <div className="space-y-1.5">
                            <div className="flex justify-between text-[11px] font-bold uppercase transition-colors">
                                <span className="text-danger flex items-center gap-1.5">
                                    <XCircle className="w-3 h-3" /> %15 Üstü (Sapma)
                                </span>
                                <span className="text-primary">{data.accuracy_distribution.error} Sefer</span>
                            </div>
                            <div className="w-full h-1.5 bg-bg-elevated rounded-full overflow-hidden border border-border">
                                <div className="h-full bg-danger shadow-sm" style={{ width: `${data.accuracy_distribution.error_pct}%` }} />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* 2. Trend Line Chart */}
            <div className="lg:col-span-2 bg-surface p-6 border border-border rounded-2xl flex flex-col shadow-sm">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h3 className="text-[10px] font-bold text-secondary uppercase tracking-widest leading-none">Tahmin Analizi</h3>
                        <p className="text-lg font-bold text-primary mt-1">Tahmin vs Gerçek Trend</p>
                    </div>
                    <div className="flex gap-4">
                        <div className="flex items-center gap-1.5 bg-accent/10 px-3 py-1.5 rounded-full border border-accent/20">
                            <div className="w-2 h-2 rounded-full bg-accent shadow-sm animate-pulse" />
                            <span className="text-[10px] font-bold uppercase text-accent tracking-widest">Tahmin</span>
                        </div>
                        <div className="flex items-center gap-1.5 bg-success/10 px-3 py-1.5 rounded-full border border-success/20">
                            <div className="w-2 h-2 rounded-full bg-success shadow-sm" />
                            <span className="text-[10px] font-bold uppercase text-success tracking-widest">Gerçek</span>
                        </div>
                    </div>
                </div>

                <div className="h-[280px] w-full flex-1">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data.trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--success)" stopOpacity={0.2}/>
                                    <stop offset="95%" stopColor="var(--success)" stopOpacity={0}/>
                                </linearGradient>
                                <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.2}/>
                                    <stop offset="95%" stopColor="var(--accent)" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.3} />
                            <XAxis 
                                dataKey="date" 
                                axisLine={false}
                                tickLine={false}
                                tick={{ fontSize: 10, fontWeight: 700, fill: 'var(--text-secondary)' }}
                                tickFormatter={(val) => new Date(val).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}
                                opacity={0.5}
                            />
                            <YAxis 
                                axisLine={false}
                                tickLine={false}
                                tick={{ fontSize: 10, fontWeight: 700, fill: 'var(--text-secondary)' }}
                                opacity={0.5}
                            />
                            <Tooltip 
                                contentStyle={{ 
                                    backgroundColor: 'var(--surface)',
                                    borderRadius: '12px', 
                                    border: '1px solid var(--border)', 
                                    boxShadow: 'var(--shadow-lg)',
                                    padding: '12px'
                                }}
                                itemStyle={{ color: 'var(--text-primary)', fontSize: '12px', fontWeight: 700 }}
                                labelStyle={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '1px' }}
                            />
                            <Area 
                                type="monotone" 
                                dataKey="predicted" 
                                name="Tahmin"
                                stroke="var(--accent)" 
                                strokeWidth={3}
                                fillOpacity={0.1} 
                                fill="var(--accent)" 
                            />
                            <Area 
                                type="monotone" 
                                dataKey="actual" 
                                name="Gerçek"
                                stroke="var(--success)" 
                                strokeWidth={3}
                                fillOpacity={0.1} 
                                fill="var(--success)" 
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                <div className="mt-6 p-4 bg-bg-elevated/50 rounded-2xl flex items-center gap-3 border border-border">
                    <Info className="w-5 h-5 text-secondary shrink-0" />
                    <p className="text-[10px] font-bold text-secondary leading-relaxed uppercase tracking-tight">
                        Bu grafik son <span className="text-primary">{data.total_compared}</span> seferden alınan verilerle oluşturulmuştur. 
                        MAE (Hata) değeri sıfıra yaklaştıkça model doğruluğu artar.
                    </p>
                </div>
            </div>
        </div>
    );
};
