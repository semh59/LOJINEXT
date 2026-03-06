import { RouteAnalysis } from '../../types/location';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Map, Activity, ArrowUpRight, ArrowDownRight, Minus, Sparkles, Bot } from 'lucide-react';
import { motion } from 'framer-motion';

interface RouteAnalysisCardProps {
    analysis: RouteAnalysis;
}

export function RouteAnalysisCard({ analysis }: RouteAnalysisCardProps) {
    // 1. Elevation / Steepness Data
    const hFlat = analysis.highway?.flat || 0;
    const hUp = analysis.highway?.up || 0;
    const hDown = analysis.highway?.down || 0;
    
    const oFlat = analysis.other?.flat || 0;
    const oUp = analysis.other?.up || 0;
    const oDown = analysis.other?.down || 0;

    const highwayTotal = hFlat + hUp + hDown;
    const otherTotal = oFlat + oUp + oDown;
    const totalDistance = highwayTotal + otherTotal || 1;

    const totalFlat = hFlat + oFlat;
    const totalUp = hUp + oUp;
    const totalDown = hDown + oDown;

    const steepnessData = [
        { name: 'Düz', value: totalFlat, color: '#22c55e', icon: Minus },
        { name: 'Çıkış', value: totalUp, color: '#ef4444', icon: ArrowUpRight },
        { name: 'İniş', value: totalDown, color: '#f59e0b', icon: ArrowDownRight }
    ].filter(d => d.value > 0);

    // 2. Road Type Data (3-Tier Distribution)
    const ratios = analysis.ratios || { otoyol: 0, devlet_yolu: 0, sehir_ici: 0 };
    const threeTierData = [
        { name: 'Otoyol', value: ratios.otoyol, color: '#3b82f6', speed: '85 km/h' },
        { name: 'Devlet Yolu', value: ratios.devlet_yolu, color: '#10b981', speed: '65 km/h' },
        { name: 'Şehir İçi', value: ratios.sehir_ici, color: '#f59e0b', speed: '35 km/h' }
    ].filter(d => d.value > 0);

    return (
        <div className="bg-white rounded-[32px] border border-neutral-100 p-8 shadow-premium space-y-8">
            <div className="flex items-center justify-between border-b border-neutral-50 pb-6">
                <div className="flex items-center gap-4">
                    <div className="bg-violet-500/10 p-3 rounded-2xl">
                        <Activity className="w-6 h-6 text-violet-600" />
                    </div>
                    <div>
                        <h3 className="font-black text-neutral-900 uppercase tracking-tight">Güzergah Zekası</h3>
                        <p className="text-[10px] text-neutral-400 font-black uppercase tracking-widest">Gelişmiş Rota ve Eğim Analizi</p>
                    </div>
                </div>
                <div className="bg-neutral-100 text-neutral-500 text-[10px] font-black px-4 py-1.5 rounded-full uppercase tracking-widest border border-neutral-200/50">
                    Mapbox Intelligence v2
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                {/* 3-Tier Distribution Chart */}
                <div className="space-y-6">
                    <h4 className="text-xs font-black text-neutral-500 uppercase tracking-widest flex items-center gap-2">
                        <Map className="w-4 h-4" />
                        Yol Karakteri Dağılımı
                    </h4>
                    
                    <div className="h-64 w-full relative">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={threeTierData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={90}
                                    paddingAngle={8}
                                    dataKey="value"
                                    stroke="none"
                                >
                                    {threeTierData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip 
                                    formatter={(value: any) => [`%${(Number(value) * 100).toFixed(0)}`, 'Oran']}
                                    contentStyle={{ borderRadius: '20px', border: 'none', boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)' }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                        
                        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                            <span className="text-[10px] font-black text-neutral-400 uppercase tracking-tighter">Toplam Rota</span>
                            <span className="text-2xl font-black text-neutral-800 tracking-tighter">
                                {totalDistance.toFixed(0)}
                                <span className="text-sm font-bold ml-1">km</span>
                            </span>
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-2">
                        {threeTierData.map((item) => (
                            <div key={item.name} className="bg-neutral-50 p-3 rounded-2xl border border-neutral-100/50 text-center">
                                <div className="text-[10px] font-black uppercase tracking-tighter opacity-50 mb-1" style={{ color: item.color }}>{item.name}</div>
                                <div className="text-xs font-black text-neutral-800">%{Math.round(item.value * 100)}</div>
                                <div className="text-[9px] font-bold text-neutral-400 mt-1 uppercase">@{item.speed}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Steepness Distribution */}
                <div className="space-y-6">
                    <h4 className="text-xs font-black text-neutral-500 uppercase tracking-widest flex items-center gap-2">
                        <Activity className="w-4 h-4" />
                        Eğim ve Topografya
                    </h4>
                   
                    <div className="space-y-5 mt-4">
                        {steepnessData.map((item) => (
                            <div key={item.name} className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="flex items-center gap-3 text-xs font-black uppercase tracking-wider text-neutral-700">
                                        <div className="p-2 rounded-lg" style={{ backgroundColor: `${item.color}15` }}>
                                            <item.icon className="w-4 h-4" style={{ color: item.color }} />
                                        </div>
                                        {item.name}
                                    </span>
                                    <div className="text-right">
                                        <div className="text-sm font-black text-neutral-900 tracking-tighter">{item.value.toFixed(1)} km</div>
                                        <div className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest">%{((item.value / (totalFlat + totalUp + totalDown || 1)) * 100).toFixed(0)}</div>
                                    </div>
                                </div>
                                <div className="h-3 w-full bg-neutral-100 rounded-full overflow-hidden border border-neutral-200/20">
                                    <motion.div 
                                        initial={{ width: 0 }}
                                        animate={{ width: `${(item.value / (totalFlat + totalUp + totalDown || 1)) * 100}%` }}
                                        className="h-full rounded-full shadow-[inset_0_1px_2px_rgba(0,0,0,0.1)]"
                                        style={{ backgroundColor: item.color }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* AI Insight Box */}
            <div className="bg-violet-600 text-white rounded-3xl p-6 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-8 transform translate-x-1/4 -translate-y-1/4 opacity-10 group-hover:scale-110 transition-transform">
                    <Sparkles className="w-32 h-32" />
                </div>
                <div className="relative z-10 space-y-2">
                    <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] opacity-80">
                        <Bot className="w-4 h-4" />
                        Yapay Zeka Analiz Özeti
                    </div>
                    <p className="text-sm font-medium leading-relaxed max-w-2xl">
                        Bu rotada operasyon verimliliği için <span className="font-black text-brand-yellow">%{Math.round(ratios.otoyol * 100)} otoyol</span> kullanımı algılandı. 
                        Fizik tabanlı yakıt motorumuz, bu yol karakterini dikkate alarak <span className="font-black underline">85 km/h</span> seyir hızı ve aerodinamik sürtünme katsayılarını otomatik kalibre etti.
                    </p>
                </div>
            </div>
        </div>
    );
}
