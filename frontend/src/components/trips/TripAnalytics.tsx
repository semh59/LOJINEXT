import { FuelPerformanceAnalyticsResponse } from '../../types';
import {
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';
import { Activity, AlertTriangle, Gauge, TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';

interface TripAnalyticsProps {
    data?: FuelPerformanceAnalyticsResponse;
    isLoading?: boolean;
}

export function TripAnalytics({ data, isLoading = false }: TripAnalyticsProps) {
    if (isLoading) {
        return (
            <div className="mb-8 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-24 rounded-2xl bg-bg-elevated/5 animate-pulse border border-border" />
                ))}
            </div>
        );
    }

    if (!data || data.low_data || data.kpis.total_compared < 3) {
        return (
            <div className="bg-surface/40 backdrop-blur-xl border border-border p-12 rounded-[32px] text-center mb-8">
                <Activity className="w-12 h-12 text-secondary mx-auto mb-4" />
                <h3 className="text-primary font-bold text-lg uppercase tracking-wider">Yetersiz Veri</h3>
                <p className="text-secondary mt-2">Karsilastirma icin veri yetersiz. Tahmin ve gercek tuketim birlikte olan en az 3 sefer gerekiyor.</p>
            </div>
        );
    }

    const distributionData = [
        { name: 'Iyi', value: data.distribution.good, color: 'var(--success)' },
        { name: 'Kabul', value: data.distribution.warning, color: 'var(--warning)' },
        { name: 'Sapma', value: data.distribution.error, color: 'var(--danger)' },
    ];

    return (
        <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-8 overflow-hidden space-y-6"
        >
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                <div className="bg-surface/60 border border-border rounded-2xl p-4">
                    <div className="text-[10px] uppercase font-black tracking-wider text-secondary">MAE</div>
                    <div className="text-2xl font-black text-accent mt-1">{data.kpis.mae.toFixed(2)}</div>
                    <div className="text-[11px] text-secondary mt-1">L/100km ortalama mutlak hata</div>
                </div>
                <div className="bg-surface/60 border border-border rounded-2xl p-4">
                    <div className="text-[10px] uppercase font-black tracking-wider text-secondary">RMSE</div>
                    <div className="text-2xl font-black text-accent mt-1">{data.kpis.rmse.toFixed(2)}</div>
                    <div className="text-[11px] text-secondary mt-1">Hata dagiliminin karekoku</div>
                </div>
                <div className="bg-surface/60 border border-border rounded-2xl p-4">
                    <div className="text-[10px] uppercase font-black tracking-wider text-secondary">Karsilastirilan Sefer</div>
                    <div className="text-2xl font-black text-success mt-1">{data.kpis.total_compared}</div>
                    <div className="text-[11px] text-secondary mt-1">Tahmin + gercek verisi olan kayit</div>
                </div>
                <div className="bg-surface/60 border border-border rounded-2xl p-4">
                    <div className="text-[10px] uppercase font-black tracking-wider text-secondary">Yuksek Sapma</div>
                    <div className="text-2xl font-black text-danger mt-1">%{data.kpis.high_deviation_ratio.toFixed(1)}</div>
                    <div className="text-[11px] text-secondary mt-1">%15 ustu sapma orani</div>
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <div className="bg-surface/60 border border-border rounded-[28px] p-6">
                    <div className="flex items-center gap-2 mb-3">
                        <TrendingUp className="w-5 h-5 text-accent" />
                        <h4 className="text-primary font-bold">Tahmin vs Gercek Trend</h4>
                    </div>
                    <p className="text-[11px] text-secondary mb-3">Gun bazinda ortalama tahmin ve gercek tuketim hareketi.</p>
                    <div className="h-[260px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data.trend}>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.2} />
                                <XAxis dataKey="date" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
                                <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
                                <Tooltip 
                                    contentStyle={{ 
                                        backgroundColor: 'var(--bg-surface)', 
                                        borderColor: 'var(--border)',
                                        color: 'var(--text-primary)'
                                    }} 
                                />
                                <Line type="monotone" dataKey="predicted" stroke="var(--accent)" strokeWidth={2.5} dot={false} name="Tahmin" />
                                <Line type="monotone" dataKey="actual" stroke="var(--success)" strokeWidth={2.5} dot={false} name="Gercek" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-surface/60 border border-border rounded-[28px] p-6">
                    <div className="flex items-center gap-2 mb-3">
                        <Gauge className="w-5 h-5 text-warning" />
                        <h4 className="text-primary font-bold">Sapma Dagilimi</h4>
                    </div>
                    <p className="text-[11px] text-secondary mb-3">Iyi, kabul ve yuksek sapma siniflarinin adet dagilimi.</p>
                    <div className="h-[260px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={distributionData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.2} />
                                <XAxis dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
                                <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
                                <Tooltip />
                                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                                    {distributionData.map((entry) => (
                                        <Cell key={entry.name} fill={entry.color} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            <div className="bg-surface/60 border border-border rounded-[28px] p-6">
                <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="w-5 h-5 text-danger" />
                    <h4 className="text-primary font-bold">En Sapmali Seferler (Top 10)</h4>
                </div>
                <p className="text-[11px] text-secondary mb-3">En yuksek fark olusturan seferler ve kisa neden etiketi.</p>
                <div className="space-y-2 max-h-[260px] overflow-y-auto custom-scrollbar pr-1">
                    {data.outliers.map((item) => (
                        <div key={item.id} className="p-3 rounded-xl border border-border bg-bg-elevated flex items-center justify-between gap-3">
                            <div className="min-w-0">
                                <div className="text-sm font-bold text-primary truncate">
                                    {item.sefer_no || `Sefer #${item.id}`} - {item.plaka || 'Plaka Yok'}
                                </div>
                                <div className="text-[11px] text-secondary truncate">
                                    {item.reason_label} | Tahmin: {item.predicted.toFixed(2)} | Gercek: {item.actual.toFixed(2)}
                                </div>
                            </div>
                            <div className="text-sm font-black text-danger shrink-0">%{item.sapma_pct.toFixed(1)}</div>
                        </div>
                    ))}
                </div>
            </div>
        </motion.div>
    );
}
