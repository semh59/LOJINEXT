import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Location, AnalysisResponse } from '../../types/location';
import {
    ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
    CartesianGrid, Tooltip
} from 'recharts';
import {
    Activity, Mountain, Info, Compass,
    Clock, MapPin, CheckCircle2, Navigation, Car, Database
} from 'lucide-react';
import { useLocations } from '../../hooks/use-locations';
import { useState, useEffect, useRef } from 'react';

interface LocationAnalyzeModalProps {
    isOpen: boolean;
    onClose: () => void;
    location: Location | null;
}

export const LocationAnalyzeModal = ({ isOpen, onClose, location }: LocationAnalyzeModalProps) => {
    const { useAnalyzeLocation } = useLocations();
    const analyzeMutation = useAnalyzeLocation();
    const [result, setResult] = useState<AnalysisResponse | null>(null);

    const triggerRef = useRef(false);

    useEffect(() => {
        if (isOpen && location?.id && !result && !triggerRef.current) {
            triggerRef.current = true;
            analyzeMutation.mutate(location.id, {
                onSuccess: (data) => {
                    setResult(data);
                }
            });
        }
        if (!isOpen) {
            triggerRef.current = false;
        }
    }, [isOpen, location, result]);

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
                <div className="bg-bg-elevated rounded-3xl p-6 border border-border flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-surface shadow-sm flex items-center justify-center text-primary border border-border">
                            <Compass className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="text-xl font-black text-primary leading-none mb-2">
                                {location.cikis_yeri} → {location.varis_yeri}
                            </h3>
                            <p className="text-sm font-medium text-secondary flex items-center gap-2">
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
                        <p className="font-black text-secondary uppercase tracking-widest text-sm">OpenRouteService Verileri Alınıyor...</p>
                    </div>
                ) : result ? (
                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {/* Metrics Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="bg-surface p-5 rounded-[28px] border border-border shadow-sm">
                                <div className="text-[10px] font-black text-secondary uppercase tracking-widest mb-3 flex justify-between">
                                    Mesafe (API)
                                    <CheckCircle2 className="w-3 h-3 text-success" />
                                </div>
                                <div className="text-3xl font-black text-primary">{result.api_mesafe_km} <span className="text-sm">km</span></div>
                            </div>

                            <div className="bg-surface p-5 rounded-[28px] border border-border shadow-sm">
                                <div className="text-[10px] font-black text-secondary uppercase tracking-widest mb-3">Süre (Tahmini)</div>
                                <div className="text-3xl font-black text-primary flex items-center gap-2">
                                    <Clock className="w-5 h-5 text-secondary" />
                                    {result.api_sure_saat} <span className="text-sm">saat</span>
                                </div>
                            </div>

                            <div className="bg-surface p-5 rounded-[28px] border border-border shadow-sm">
                                <div className="text-[10px] font-black text-secondary uppercase tracking-widest mb-3">Tırmanış</div>
                                <div className="text-3xl font-black text-success flex items-center gap-2">
                                    <TrendingUpIcon size={24} className="text-success" />
                                    {result.ascent_m} <span className="text-sm">m</span>
                                </div>
                            </div>

                            <div className="bg-surface p-5 rounded-[28px] border border-border shadow-sm">
                                <div className="text-[10px] font-black text-secondary uppercase tracking-widest mb-3">İniş</div>
                                <div className="text-3xl font-black text-warning flex items-center gap-2">
                                    <TrendingDownIcon size={24} className="text-warning" />
                                    {result.descent_m} <span className="text-sm">m</span>
                                </div>
                            </div>
                        </div>

                        {/* Distance Distribution (Highway vs Urban) */}
                        <div className="bg-surface p-6 rounded-[32px] border border-border shadow-sm space-y-4">
                            <div className="flex justify-between items-end">
                                <div>
                                    <h4 className="text-sm font-black text-secondary uppercase tracking-widest mb-1">Yol Tipi Dağılımı</h4>
                                    <p className="text-xs text-secondary">Güzergahın otoban ve şehiriçi/kırsal mesafe oranı</p>
                                </div>
                                <div className="text-right">
                                    <span className="text-xs font-bold text-primary bg-bg-elevated px-3 py-1 rounded-full border border-border">
                                        Toplam: {result.api_mesafe_km} km
                                    </span>
                                </div>
                            </div>

                            <div className="relative h-6 bg-bg-elevated rounded-full overflow-hidden flex shadow-inner">
                                <div 
                                    className="h-full bg-gradient-to-r from-primary to-primary/80 relative group cursor-help transition-all duration-1000 ease-out"
                                    style={{ width: `${(result.otoban_mesafe_km / result.api_mesafe_km) * 100}%` }}
                                >
                                    <div className="absolute inset-0 bg-accent/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                                </div>
                                <div 
                                    className="h-full bg-gradient-to-r from-accent to-accent/80 transition-all duration-1000 ease-out"
                                    style={{ width: `${(result.sehir_ici_mesafe_km / result.api_mesafe_km) * 100}%` }}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex items-center gap-3 p-3 bg-bg-elevated rounded-2xl border border-border">
                                    <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center text-surface">
                                        <Navigation className="w-4 h-4" />
                                    </div>
                                    <div>
                                        <div className="text-[10px] font-black text-secondary uppercase">Otoban</div>
                                        <div className="text-lg font-black text-primary">{result.otoban_mesafe_km} <span className="text-xs">km</span></div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 p-3 bg-accent/5 rounded-2xl border border-accent/10">
                                    <div className="w-8 h-8 rounded-xl bg-accent flex items-center justify-center text-bg-base">
                                        <Car className="w-4 h-4" />
                                    </div>
                                    <div>
                                        <div className="text-[10px] font-black text-secondary uppercase">Şehiriçi / Kırsal</div>
                                        <div className="text-lg font-black text-primary">{result.sehir_ici_mesafe_km} <span className="text-xs">km</span></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Chart Area */}
                        <div className="bg-surface rounded-[40px] p-8 shadow-2xl relative overflow-hidden group border border-border">
                            <div className="absolute top-0 right-0 w-64 h-64 bg-accent/5 blur-[120px] rounded-full -mr-32 -mt-32" />
                            <div className="absolute bottom-0 left-0 w-64 h-64 bg-success/5 blur-[120px] rounded-full -ml-32 -mb-32" />

                            <div className="relative z-10">
                                <div className="flex items-center justify-between mb-8">
                                    <div>
                                        <h4 className="text-primary text-xl font-black flex items-center gap-3">
                                            <Mountain className="w-6 h-6 text-accent" />
                                            Yükseklik Profili
                                        </h4>
                                        <p className="text-secondary text-sm font-medium">Güzergah boyunca rakım değişimi (Metre)</p>
                                    </div>
                                    <div className="bg-bg-elevated/50 border border-border px-4 py-2 rounded-2xl backdrop-blur-md">
                                        <span className="text-xs font-black text-secondary uppercase tracking-widest">Çözünürlük: Yüksek</span>
                                    </div>
                                </div>

                                <div className="h-[300px] w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={result.elevation_profile}>
                                            <defs>
                                                <linearGradient id="elevationColor" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.4} />
                                                    <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.3} vertical={false} />
                                            <XAxis
                                                dataKey="distance_km"
                                                stroke="var(--text-secondary)"
                                                fontSize={11}
                                                tickFormatter={(val) => `${val}km`}
                                                axisLine={false}
                                                tickLine={false}
                                                opacity={0.5}
                                            />
                                            <YAxis
                                                stroke="var(--text-secondary)"
                                                fontSize={11}
                                                tickFormatter={(val) => `${val}m`}
                                                axisLine={false}
                                                tickLine={false}
                                                opacity={0.5}
                                            />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '16px', color: 'var(--text-primary)' }}
                                                itemStyle={{ color: 'var(--accent)' }}
                                                formatter={(value) => [`${value}m`, 'Yükseklik']}
                                                labelFormatter={(label) => `${label} km`}
                                            />
                                            <Area
                                                type="monotone"
                                                dataKey="elevation_m"
                                                stroke="var(--accent)"
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

                        <div className="flex items-start gap-4 p-5 bg-info/10 rounded-2xl border border-info/20 relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-3 opacity-20 group-hover:opacity-40 transition-opacity">
                                <Database className="w-12 h-12 text-info" />
                            </div>
                            <div className="relative z-10 flex gap-4">
                                <Info className="w-5 h-5 text-info shrink-0 mt-0.5" />
                                <div className="space-y-1">
                                    <p className="text-sm font-bold text-info">
                                        Veri Kaynağı: <span className="text-accent uppercase tracking-tighter">{result.source || 'OpenRouteService'}</span>
                                    </p>
                                    <p className="text-xs font-medium text-info leading-relaxed">
                                        Bu analiz <strong>{result.source?.includes('mapbox') ? 'Mapbox Directions' : 'OpenRouteService'}</strong> tarafından sağlanan veriler kullanılarak yapılmıştır.
                                        Toplam tırmanış ({result.ascent_m}m), yakıt tüketimini doğrudan etkileyen bir faktördür.
                                    </p>
                                    {result.is_corrected && (
                                        <div className="mt-3 p-3 bg-warning/10 border border-warning/20 rounded-xl flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-warning flex items-center justify-center text-bg-base shrink-0">
                                                <TrendingUpIcon size={18} />
                                            </div>
                                            <div>
                                                <div className="text-[10px] font-black text-warning uppercase tracking-widest">Akıllı Düzeltme Uygulandı</div>
                                                <div className="text-xs font-bold text-warning/90">{result.correction_reason}</div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="py-20 text-center text-secondary">
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
