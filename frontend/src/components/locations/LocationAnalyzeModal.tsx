import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Location, AnalysisResponse } from '../../types/location';
import {
    ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
    CartesianGrid, Tooltip
} from 'recharts';
import {
    Activity, Mountain, Info, Compass,
    Clock, MapPin, CheckCircle2
} from 'lucide-react';
import { useLocations } from '../../hooks/use-locations';
import { useState, useEffect } from 'react';

interface LocationAnalyzeModalProps {
    isOpen: boolean;
    onClose: () => void;
    location: Location | null;
}

export const LocationAnalyzeModal = ({ isOpen, onClose, location }: LocationAnalyzeModalProps) => {
    const { useAnalyzeLocation } = useLocations();
    const analyzeMutation = useAnalyzeLocation();
    const [result, setResult] = useState<AnalysisResponse | null>(null);

    useEffect(() => {
        if (isOpen && location?.id && !result) {
            analyzeMutation.mutate(location.id, {
                onSuccess: (data) => {
                    setResult(data);
                }
            });
        }
    }, [isOpen, location, analyzeMutation, result]);

    // Re-trigger analysis if user wants
    const handleReAnalyze = () => {
        if (location?.id) {
            analyzeMutation.mutate(location.id, {
                onSuccess: (data) => setResult(data)
            });
        }
    };

    if (!location) return null;

    const isLoading = analyzeMutation.isPending;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={
                <div className="flex items-center gap-2">
                    <Activity className="w-6 h-6 text-primary" />
                    <span>Akıllı Güzergah Analizi</span>
                </div>
            }
            size="xl"
            className="overflow-hidden"
        >
            <div className="space-y-8">
                {/* Header Info */}
                <div className="bg-neutral-50 rounded-3xl p-6 border border-neutral-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-white shadow-sm flex items-center justify-center text-primary border border-neutral-200">
                            <Compass className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="text-xl font-black text-neutral-900 leading-none mb-2">
                                {location.cikis_yeri} → {location.varis_yeri}
                            </h3>
                            <p className="text-sm font-medium text-neutral-500 flex items-center gap-2">
                                <MapPin className="w-3.5 h-3.5" />
                                {location.mesafe_km} km mesafe kayıtlı
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <Button variant="secondary" onClick={handleReAnalyze} disabled={isLoading}>
                            Tekrar Analiz Et
                        </Button>
                        <Button onClick={onClose}>Kapat</Button>
                    </div>
                </div>

                {isLoading ? (
                    <div className="py-20 flex flex-col items-center justify-center space-y-4">
                        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                        <p className="font-black text-neutral-400 uppercase tracking-widest text-sm">OpenRouteService Verileri Alınıyor...</p>
                    </div>
                ) : result ? (
                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {/* Metrics Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="bg-white p-5 rounded-[28px] border border-neutral-200 shadow-sm">
                                <div className="text-[10px] font-black text-neutral-400 uppercase tracking-widest mb-3 flex justify-between">
                                    Mesafe (API)
                                    <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                                </div>
                                <div className="text-3xl font-black text-neutral-900">{result.api_mesafe_km} <span className="text-sm">km</span></div>
                            </div>

                            <div className="bg-white p-5 rounded-[28px] border border-neutral-200 shadow-sm">
                                <div className="text-[10px] font-black text-neutral-400 uppercase tracking-widest mb-3">Süre (Tahmini)</div>
                                <div className="text-3xl font-black text-neutral-900 flex items-center gap-2">
                                    <Clock className="w-5 h-5 text-neutral-300" />
                                    {result.api_sure_saat} <span className="text-sm">saat</span>
                                </div>
                            </div>

                            <div className="bg-white p-5 rounded-[28px] border border-neutral-200 shadow-sm">
                                <div className="text-[10px] font-black text-neutral-400 uppercase tracking-widest mb-3">Tırmanış</div>
                                <div className="text-3xl font-black text-emerald-600 flex items-center gap-2">
                                    <TrendingUpIcon size={24} className="text-emerald-500" />
                                    {result.ascent_m} <span className="text-sm">m</span>
                                </div>
                            </div>

                            <div className="bg-white p-5 rounded-[28px] border border-neutral-200 shadow-sm">
                                <div className="text-[10px] font-black text-neutral-400 uppercase tracking-widest mb-3">İniş</div>
                                <div className="text-3xl font-black text-amber-600 flex items-center gap-2">
                                    <TrendingDownIcon size={24} className="text-amber-500" />
                                    {result.descent_m} <span className="text-sm">m</span>
                                </div>
                            </div>
                        </div>

                        {/* Chart Area */}
                        <div className="bg-neutral-900 rounded-[40px] p-8 shadow-2xl relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/20 blur-[120px] rounded-full -mr-32 -mt-32" />
                            <div className="absolute bottom-0 left-0 w-64 h-64 bg-emerald-500/10 blur-[120px] rounded-full -ml-32 -mb-32" />

                            <div className="relative z-10">
                                <div className="flex items-center justify-between mb-8">
                                    <div>
                                        <h4 className="text-white text-xl font-black flex items-center gap-3">
                                            <Mountain className="w-6 h-6 text-primary" />
                                            Yükseklik Profili
                                        </h4>
                                        <p className="text-neutral-400 text-sm font-medium">Güzergah boyunca rakım değişimi (Metre)</p>
                                    </div>
                                    <div className="bg-white/5 border border-white/10 px-4 py-2 rounded-2xl backdrop-blur-md">
                                        <span className="text-xs font-black text-neutral-400 uppercase tracking-widest">Çözünürlük: Yüksek</span>
                                    </div>
                                </div>

                                <div className="h-[300px] w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={result.elevation_profile}>
                                            <defs>
                                                <linearGradient id="elevationColor" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#FB6F3E" stopOpacity={0.4} />
                                                    <stop offset="95%" stopColor="#FB6F3E" stopOpacity={0} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                                            <XAxis
                                                dataKey="distance_km"
                                                stroke="#ffffff40"
                                                fontSize={11}
                                                tickFormatter={(val) => `${val}km`}
                                                axisLine={false}
                                                tickLine={false}
                                            />
                                            <YAxis
                                                stroke="#ffffff40"
                                                fontSize={11}
                                                tickFormatter={(val) => `${val}m`}
                                                axisLine={false}
                                                tickLine={false}
                                            />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#171717', border: '1px solid #333', borderRadius: '16px', color: '#fff' }}
                                                itemStyle={{ color: '#FB6F3E' }}
                                                formatter={(value) => [`${value}m`, 'Yükseklik']}
                                                labelFormatter={(label) => `${label} km`}
                                            />
                                            <Area
                                                type="monotone"
                                                dataKey="elevation_m"
                                                stroke="#FB6F3E"
                                                strokeWidth={3}
                                                fillOpacity={1}
                                                fill="url(#elevationColor)"
                                                animationDuration={2000}
                                            />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-start gap-4 p-5 bg-blue-50/50 rounded-2xl border border-blue-100">
                            <Info className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
                            <p className="text-xs font-medium text-blue-700 leading-relaxed">
                                <strong>Smart Tip:</strong> Bu analiz OpenRouteService tarafından sağlanan topografik veriler kullanılarak yapılmıştır.
                                Toplam tırmanış ({result.ascent_m}m), yakıt tüketimini doğrudan etkileyen bir faktördür.
                            </p>
                        </div>
                    </div>
                ) : (
                    <div className="py-20 text-center text-neutral-400">
                        Analiz verisi bulunamadı.
                    </div>
                )}
            </div>
        </Modal>
    );
};

// Lucide icons defined inline for cleaner usage
const TrendingUpIcon = ({ size, className }: { size?: number, className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={size || 24} height={size || 24} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className={className}><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline><polyline points="16 7 22 7 22 13"></polyline></svg>
);

const TrendingDownIcon = ({ size, className }: { size?: number, className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={size || 24} height={size || 24} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className={className}><polyline points="22 17 13.5 8.5 8.5 13.5 2 7"></polyline><polyline points="16 17 22 17 22 11"></polyline></svg>
);
