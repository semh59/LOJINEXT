import { motion } from 'framer-motion';
import { Location } from '../../types/location';
import {
    Edit2, Trash2, BarChart,
    ArrowRight, MapPin, Wind, TrendingUp, Mountain
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { Button } from '../ui/Button';

interface LocationListProps {
    locations: Location[];
    loading: boolean;
    onEdit: (location: Location) => void;
    onDelete: (location: Location) => void;
    onAnalyze: (location: Location) => void;
    viewMode: 'table' | 'grid';
}

const getDifficultyConfig = (difficulty: string) => {
    switch (difficulty) {
        case 'Zor':
            return {
                label: 'Dağlık',
                icon: <Mountain className="w-3 h-3" />,
                bg: 'bg-red-100 text-red-700 border-red-200',
                dot: 'bg-red-500'
            };
        case 'Orta':
            return {
                label: 'Eğimli',
                icon: <TrendingUp className="w-3 h-3" />,
                bg: 'bg-amber-100 text-amber-700 border-amber-200',
                dot: 'bg-amber-500'
            };
        default:
            return {
                label: 'Düz',
                icon: <Wind className="w-3 h-3" />,
                bg: 'bg-emerald-100 text-emerald-700 border-emerald-200',
                dot: 'bg-emerald-500'
            };
    }
};

const SkeletonRow = () => (
    <tr className="animate-pulse border-b border-neutral-100">
        <td className="px-6 py-4"><div className="h-4 bg-neutral-200 rounded w-24" /></td>
        <td className="px-6 py-4"><div className="h-4 bg-neutral-200 rounded w-24" /></td>
        <td className="px-6 py-4"><div className="h-4 bg-neutral-200 rounded w-16" /></td>
        <td className="px-6 py-4"><div className="h-4 bg-neutral-200 rounded w-12" /></td>
        <td className="px-6 py-4"><div className="h-4 bg-neutral-200 rounded w-20" /></td>
        <td className="px-6 py-4 text-right"><div className="h-8 bg-neutral-200 rounded w-8 inline-block" /></td>
    </tr>
);

export const LocationList = ({ locations, loading, onEdit, onDelete, onAnalyze, viewMode }: LocationListProps) => {
    if (loading && locations.length === 0) {
        if (viewMode === 'table') {
            return (
                <div className="bg-white rounded-3xl border border-neutral-200 overflow-hidden">
                    <table className="w-full text-left">
                        <thead className="bg-neutral-50 border-b border-neutral-200">
                            <tr>
                                <th className="px-6 py-4 text-xs font-black text-neutral-400 uppercase tracking-widest">Çıkış</th>
                                <th className="px-6 py-4 text-xs font-black text-neutral-400 uppercase tracking-widest">Varış</th>
                                <th className="px-6 py-4 text-xs font-black text-neutral-400 uppercase tracking-widest">Mesafe</th>
                                <th className="px-6 py-4 text-xs font-black text-neutral-400 uppercase tracking-widest">Süre</th>
                                <th className="px-6 py-4 text-xs font-black text-neutral-400 uppercase tracking-widest">Zorluk</th>
                                <th className="px-6 py-4 text-right"></th>
                            </tr>
                        </thead>
                        <tbody>
                            {[1, 2, 3, 4, 5].map(i => <SkeletonRow key={i} />)}
                        </tbody>
                    </table>
                </div>
            );
        }
    }

    if (locations.length === 0 && !loading) {
        return (
            <div className="flex flex-col items-center justify-center py-20 px-6 bg-white rounded-[40px] border border-dashed border-neutral-300">
                <div className="w-20 h-20 bg-neutral-100 rounded-full flex items-center justify-center mb-6">
                    <MapPin className="w-10 h-10 text-neutral-400" />
                </div>
                <h3 className="text-2xl font-black text-neutral-900 mb-2">Henüz Güzergah Yok</h3>
                <p className="text-neutral-500 font-medium text-center max-w-sm mb-8">
                    Sistemde kayıtlı güzergah bulunamadı. Hemen bir tane ekleyerek başlayın.
                </p>
                <Button onClick={() => { }}>Güzergah Ekle</Button>
            </div>
        );
    }

    if (viewMode === 'table') {
        return (
            <div className="bg-white rounded-[32px] border border-neutral-200 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-neutral-50/50 border-b border-neutral-200">
                                <th className="px-6 py-5 text-[11px] font-black text-neutral-400 uppercase tracking-widest">Çıkış Noktası</th>
                                <th className="px-6 py-5 text-[11px] font-black text-neutral-400 uppercase tracking-widest">Varış Noktası</th>
                                <th className="px-6 py-5 text-[11px] font-black text-neutral-400 uppercase tracking-widest">Mesafe</th>
                                <th className="px-6 py-5 text-[11px] font-black text-neutral-400 uppercase tracking-widest">Süre</th>
                                <th className="px-6 py-5 text-[11px] font-black text-neutral-400 uppercase tracking-widest">Zorluk / Eğim</th>
                                <th className="px-6 py-5 text-right">İşlemler</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-neutral-100">
                            {locations.map((loc, index) => {
                                const difficulty = getDifficultyConfig(loc.zorluk);
                                return (
                                    <motion.tr
                                        key={loc.id}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: index * 0.05 }}
                                        className="group hover:bg-neutral-50/50 transition-colors"
                                    >
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-xl bg-primary/5 flex items-center justify-center text-primary border border-primary/10">
                                                    <MapPin className="w-5 h-5" />
                                                </div>
                                                <span className="font-bold text-neutral-900 underline decoration-primary/20 underline-offset-4">{loc.cikis_yeri}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <ArrowRight className="w-4 h-4 text-neutral-300" />
                                                <span className="font-bold text-neutral-900">{loc.varis_yeri}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col">
                                                <span className="font-black text-neutral-900">{loc.mesafe_km} km</span>
                                                {loc.api_mesafe_km && (
                                                    <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-tight">API: {loc.api_mesafe_km} km</span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="font-bold text-neutral-600 bg-neutral-100 px-3 py-1 rounded-lg">{loc.tahmini_sure_saat}s</span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <span className={cn(
                                                    "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-black uppercase tracking-wider border",
                                                    difficulty.bg
                                                )}>
                                                    {difficulty.icon}
                                                    {difficulty.label}
                                                </span>
                                                <div className="flex flex-col text-[10px] font-black text-neutral-400 uppercase">
                                                    <span>↑ {loc.ascent_m || 0}m</span>
                                                    <span>↓ {loc.descent_m || 0}m</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    onClick={() => onAnalyze(loc)}
                                                    className="p-2.5 rounded-xl bg-primary/5 text-primary hover:bg-primary hover:text-white transition-all border border-primary/10"
                                                    title="Analiz Et"
                                                >
                                                    <BarChart className="w-4 h-4" />
                                                </button>
                                                <button
                                                    onClick={() => onEdit(loc)}
                                                    className="p-2.5 rounded-xl bg-neutral-100 text-neutral-500 hover:bg-neutral-900 hover:text-white transition-all border border-neutral-200"
                                                    title="Düzenle"
                                                >
                                                    <Edit2 className="w-4 h-4" />
                                                </button>
                                                <button
                                                    onClick={() => onDelete(loc)}
                                                    className="p-2.5 rounded-xl bg-red-50 text-red-500 hover:bg-red-500 hover:text-white transition-all border border-red-100"
                                                    title="Sil"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </motion.tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    }

    // Grid View
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {locations.map((loc, index) => {
                const difficulty = getDifficultyConfig(loc.zorluk);
                return (
                    <motion.div
                        key={loc.id}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.05 }}
                        className="bg-white rounded-[32px] p-6 border border-neutral-200 shadow-sm hover:shadow-xl hover:shadow-primary/5 transition-all group"
                    >
                        <div className="flex justify-between items-start mb-6">
                            <span className={cn(
                                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border",
                                difficulty.bg
                            )}>
                                {difficulty.icon}
                                {difficulty.label}
                            </span>
                            <div className="flex gap-2">
                                <button onClick={() => onEdit(loc)} className="p-2 rounded-xl bg-neutral-50 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-900 transition-colors">
                                    <Edit2 className="w-4 h-4" />
                                </button>
                                <button onClick={() => onDelete(loc)} className="p-2 rounded-xl bg-red-50 text-red-300 hover:bg-red-100 hover:text-red-600 transition-colors">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>

                        <div className="space-y-4 mb-6">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center text-primary shrink-0">
                                    <MapPin className="w-5 h-5" />
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-xs font-black text-neutral-400 uppercase tracking-widest">Çıkış</span>
                                    <span className="text-xl font-black text-neutral-900 tracking-tight">{loc.cikis_yeri}</span>
                                </div>
                            </div>

                            <div className="pl-5 border-l-2 border-dashed border-neutral-100 my-1 py-1">
                                <div className="w-2 h-2 rounded-full bg-primary/20 -ml-[25px]" />
                            </div>

                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-2xl bg-neutral-100 flex items-center justify-center text-neutral-400 shrink-0">
                                    <MapPin className="w-5 h-5" />
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-xs font-black text-neutral-400 uppercase tracking-widest">Varış</span>
                                    <span className="text-xl font-black text-neutral-900 tracking-tight">{loc.varis_yeri}</span>
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 pt-6 border-t border-neutral-100">
                            <div className="flex flex-col bg-neutral-50/50 p-4 rounded-2xl border border-neutral-100">
                                <span className="text-[10px] font-black text-neutral-400 uppercase tracking-widest mb-1">Mesafe</span>
                                <span className="text-xl font-black text-neutral-900">{loc.mesafe_km} <span className="text-xs text-neutral-400">km</span></span>
                            </div>
                            <div className="flex flex-col bg-neutral-50/50 p-4 rounded-2xl border border-neutral-100">
                                <span className="text-[10px] font-black text-neutral-400 uppercase tracking-widest mb-1">Süre</span>
                                <span className="text-xl font-black text-neutral-900">{loc.tahmini_sure_saat} <span className="text-xs text-neutral-400">saat</span></span>
                            </div>
                        </div>

                        <Button
                            className="w-full mt-6 bg-primary/5 text-primary hover:bg-primary hover:text-white border-primary/10"
                            onClick={() => onAnalyze(loc)}
                        >
                            <BarChart className="w-4 h-4 mr-2" />
                            Rotayı Analiz Et
                        </Button>
                    </motion.div>
                );
            })}
        </div>
    );
};
