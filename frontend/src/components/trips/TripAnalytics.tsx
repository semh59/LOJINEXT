import { useMemo } from 'react';
import { 
    ScatterChart, Scatter, XAxis, YAxis, ZAxis, 
    CartesianGrid, Tooltip, ResponsiveContainer, 
    LineChart, Line
} from 'recharts';
import { motion } from 'framer-motion';
import { Trip } from '../../types';
import { TrendingUp, Activity, AlertTriangle } from 'lucide-react';

interface TripAnalyticsProps {
    trips: Trip[];
}

export function TripAnalytics({ trips }: TripAnalyticsProps) {
    // 1. Data Processing for Scatter Plot (Distance vs Consumption)
    const scatterData = useMemo(() => {
        return trips
            .filter(t => t.mesafe_km && t.tuketim)
            .map(t => {
                const isOutlier = t.tahmini_tuketim ? (t.tuketim! > t.tahmini_tuketim * 1.25) : false;
                return {
                    id: t.id,
                    x: t.mesafe_km,
                    y: t.tuketim,
                    z: 50,
                    outlier: isOutlier,
                    name: t.plaka || t.sefer_no
                };
            });
    }, [trips]);

    // 2. Data Processing for Trend Plot (Fuel Efficiency over Time)
    const trendData = useMemo(() => {
        const dailyGroups: Record<string, { totalKm: number; totalL: number }> = {};
        
        trips.forEach(t => {
            if (!t.tarih || !t.mesafe_km || !t.tuketim) return;
            const date = new Date(t.tarih).toLocaleDateString('tr-TR');
            if (!dailyGroups[date]) {
                dailyGroups[date] = { totalKm: 0, totalL: 0 };
            }
            dailyGroups[date].totalKm += t.mesafe_km;
            dailyGroups[date].totalL += t.tuketim;
        });

        return Object.entries(dailyGroups)
            .map(([date, data]) => ({
                date,
                efficiency: data.totalKm > 0 ? (data.totalL / data.totalKm) * 100 : 0
            }))
            .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    }, [trips]);

    if (trips.length < 3) {
        return (
            <div className="bg-[#132326]/40 backdrop-blur-xl border border-white/5 p-12 rounded-[32px] text-center mb-8">
                <Activity className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                <h3 className="text-white font-bold text-lg uppercase tracking-wider">Yetersiz Veri</h3>
                <p className="text-slate-500 mt-2">Analiz oluşturmak için en az 3 tamamlanmış sefer gereklidir.</p>
            </div>
        );
    }

    return (
        <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-8 overflow-hidden"
        >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 1. Outlier Detection Scatter Plot */}
                <div className="glass-card bg-[#132326]/60 backdrop-blur-xl border border-white/5 p-6 rounded-[32px]">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-amber-500/10 rounded-xl flex items-center justify-center">
                                <AlertTriangle className="w-6 h-6 text-amber-500" />
                            </div>
                            <div>
                                <h4 className="text-white font-bold">Performans Dağılımı & Anomaliler</h4>
                                <p className="text-slate-400 text-[10px] uppercase tracking-wider font-bold italic">Mesafe (km) vs Toplam Tüketim (L)</p>
                            </div>
                        </div>
                    </div>
                    
                    <div className="h-[300px] w-full mt-4">
                        <p className="text-[10px] text-slate-500 mb-2 italic">**Bilgi:** Pembe noktalar, tahminden %25'ten fazla sapan seferleri gösterir.</p>
                        <ResponsiveContainer width="100%" height="100%">
                            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                                <XAxis 
                                    type="number" 
                                    dataKey="x" 
                                    name="Yol Mesafesi" 
                                    unit=" km" 
                                    stroke="#55666b" 
                                    fontSize={10} 
                                    fontWeight="bold"
                                />
                                <YAxis 
                                    type="number" 
                                    dataKey="y" 
                                    name="Gerçek Tüketim" 
                                    unit=" L" 
                                    stroke="#55666b" 
                                    fontSize={10} 
                                    fontWeight="bold"
                                />
                                <ZAxis type="number" dataKey="z" range={[60, 400]} name="Yoğunluk" />
                                <Tooltip 
                                    cursor={{ strokeDasharray: '3 3' }} 
                                    contentStyle={{ backgroundColor: '#132326', border: '1px solid #ffffff10', borderRadius: '12px' }}
                                    formatter={(value: any, name: any) => [value, name]}
                                />
                                <Scatter name="Standart Sefer" data={scatterData.filter(d => !d.outlier)} fill="#25d1f4" fillOpacity={0.8} />
                                <Scatter name="Anomal Sefer" data={scatterData.filter(d => d.outlier)} fill="#f43f5e" fillOpacity={0.9} />
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* 2. Fuel Efficiency Trend */}
                <div className="glass-card bg-[#132326]/60 backdrop-blur-xl border border-white/5 p-6 rounded-[32px]">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-[#25d1f4]/10 rounded-xl flex items-center justify-center">
                                <TrendingUp className="w-6 h-6 text-[#25d1f4]" />
                            </div>
                            <div>
                                <h4 className="text-white font-bold">Yakıt Verimliliği Trendi</h4>
                                <p className="text-slate-400 text-[10px] uppercase tracking-wider font-bold italic">L/100km (Günlük Ortalama)</p>
                            </div>
                        </div>
                    </div>

                    <div className="h-[300px] w-full mt-4">
                        <p className="text-[10px] text-slate-500 mb-2 italic">**Bilgi:** Tüm operasyonun günlük ağırlıklı ortalama tüketim trendi.</p>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={trendData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                                <XAxis 
                                    dataKey="date" 
                                    stroke="#55666b" 
                                    fontSize={10} 
                                    fontWeight="bold"
                                />
                                <YAxis 
                                    stroke="#55666b" 
                                    fontSize={10} 
                                    fontWeight="bold"
                                    unit=" L/100"
                                />
                                <Tooltip 
                                    contentStyle={{ backgroundColor: '#132326', border: '1px solid #ffffff10', borderRadius: '12px' }}
                                    formatter={(value: any) => [`${Number(value).toFixed(2)} L/100km`, 'Verimlilik']}
                                />
                                <Line 
                                    name="Verimlilik"
                                    type="monotone" 
                                    dataKey="efficiency" 
                                    stroke="#25d1f4" 
                                    strokeWidth={3} 
                                    dot={{ r: 4, fill: '#25d1f4', strokeWidth: 2, stroke: '#000' }}
                                    activeDot={{ r: 6 }} 
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
