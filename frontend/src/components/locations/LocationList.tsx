import { motion } from 'framer-motion';
import { Location } from '../../types/location';
import {
    Edit2, Trash2,
    ArrowRight, MapPin, Database, Mountain, TrendingUp, Wind
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { Button } from '../ui/Button';

interface LocationListProps {
    locations: Location[];
    loading: boolean;
    onEdit: (location: Location) => void;
    onDelete: (location: Location) => void;
    onAnalyze: (location: Location) => void;
    onAdd: () => void;
    viewMode: 'table' | 'grid'; // Kept for prop compatibility but only table is rendered
}

const getDifficultyConfig = (difficulty: string) => {
    switch (difficulty) {
        case 'Zor':
            return {
                label: 'Dağlık',
                icon: <Mountain className="w-3 h-3" />,
                bg: 'bg-red-500/10 text-red-500 border-red-500/20',
                dot: 'bg-red-500'
            };
        case 'Orta':
            return {
                label: 'Eğimli',
                icon: <TrendingUp className="w-3 h-3" />,
                bg: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
                dot: 'bg-amber-500'
            };
        default:
            return {
                label: 'Düz',
                icon: <Wind className="w-3 h-3" />,
                bg: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
                dot: 'bg-emerald-500'
            };
    }
};

const getSourceConfig = (source: string | undefined) => {
    switch (source?.toLowerCase()) {
        case 'mapbox_hybrid':
        case 'mapbox':
            return {
                label: 'Sistem-V2',
                bg: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
                icon: <Database className="w-3 h-3" />
            };
        case 'api':
        case 'openrouteservice':
            return {
                label: 'Sistem-V1',
                bg: 'bg-violet-500/10 text-violet-500 border-violet-500/20',
                icon: <Database className="w-3 h-3" />
            };
        case 'cache':
            return {
                label: 'Önbellek',
                bg: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
                icon: <Database className="w-3 h-3" />
            };
        default:
            return {
                label: 'Sistem',
                bg: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
                icon: <Database className="w-3 h-3" />
            };
    }
};

const SkeletonRow = () => (
    <tr className="animate-pulse border-b border-[#482923]/50">
        <td className="px-6 py-4"><div className="h-4 bg-[#331e19] rounded w-24" /></td>
        <td className="px-6 py-4"><div className="h-4 bg-[#331e19] rounded w-24" /></td>
        <td className="px-6 py-4"><div className="h-4 bg-[#331e19] rounded w-16" /></td>
        <td className="px-6 py-4"><div className="h-4 bg-[#331e19] rounded w-12" /></td>
        <td className="px-6 py-4"><div className="h-4 bg-[#331e19] rounded w-20" /></td>
        <td className="px-6 py-4 text-right"><div className="h-8 bg-[#331e19] rounded-lg w-20 ml-auto" /></td>
    </tr>
);

export function LocationList({ locations, loading, onEdit, onDelete, onAnalyze, onAdd }: LocationListProps) {
    if (loading) {
        return (
            <div className="bg-[#331e19]/40 backdrop-blur-md rounded-xl border border-[#482923] shadow-sm overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead className="text-[#c99b92] text-xs uppercase tracking-wider bg-[#221411]/50 border-b border-[#482923]">
                        <tr>
                            <th className="px-6 py-4 font-medium">Güzargah Bilgisi</th>
                            <th className="px-6 py-4 font-medium">Varış Noktası</th>
                            <th className="px-6 py-4 font-medium">Mesafe</th>
                            <th className="px-6 py-4 font-medium">Zorluk Seviyesi</th>
                            <th className="px-6 py-4 font-medium">Teknik Veriler</th>
                            <th className="px-6 py-4 font-medium text-right">İşlemler</th>
                        </tr>
                    </thead>
                    <tbody>
                        {[1, 2, 3, 4, 5].map(i => <SkeletonRow key={i} />)}
                    </tbody>
                </table>
            </div>
        );
    }

    if (locations.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-20 px-4 text-center bg-[#331e19]/40 backdrop-blur-md rounded-xl border-2 border-dashed border-[#482923]">
                <div className="w-20 h-20 rounded-full bg-[#221411] flex items-center justify-center mb-6 border border-[#482923]">
                    <MapPin className="w-10 h-10 text-[#c99b92]" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">Güzergah Bulunamadı</h3>
                <p className="text-[#c99b92] max-w-md mb-8">
                    Arama kriterlerinize uygun güzergah bulunamadı veya henüz hiç güzergah eklenmemiş.
                </p>
                <button onClick={onAdd} className="flex items-center gap-2 bg-[#ec3713] hover:bg-red-600 text-white font-bold py-2.5 px-6 rounded-lg shadow-lg transition-all">
                    <ArrowRight className="w-5 h-5" />
                    İlk Güzergahı Ekle
                </button>
            </div>
        );
    }

    return (
        <div className="bg-[#331e19]/40 backdrop-blur-md rounded-xl border border-[#482923] shadow-sm overflow-hidden flex flex-col flex-1 min-h-0">
            <div className="p-4 border-b border-[#482923] flex items-center justify-between">
                <h3 className="text-white text-lg font-bold">Kayıtlı Güzergahlar</h3>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="text-[#c99b92] text-xs uppercase tracking-wider bg-[#221411]/50 border-b border-[#482923]">
                        <tr>
                            <th className="px-6 py-4 font-medium">Güzargah Bilgisi</th>
                            <th className="px-6 py-4 font-medium">Varış Noktası</th>
                            <th className="px-6 py-4 font-medium">Mesafe</th>
                            <th className="px-6 py-4 font-medium">Zorluk Seviyesi</th>
                            <th className="px-6 py-4 font-medium">Teknik Veriler</th>
                            <th className="px-6 py-4 font-medium text-right">İşlemler</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[#482923]/50 text-sm text-white">
                        {locations.map((loc, index) => {
                            const difficulty = getDifficultyConfig(loc.zorluk);
                            const source = getSourceConfig(loc.source);
                            return (
                                <motion.tr
                                    key={loc.id}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.03 }}
                                    className="hover:bg-[#482923]/30 transition-colors group"
                                >
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="size-8 rounded-lg bg-[#221411] border border-[#482923] flex items-center justify-center text-[#ec3713]">
                                                <MapPin className="w-4 h-4" />
                                            </div>
                                            <span className="font-bold text-white tracking-wide">{loc.cikis_yeri}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2">
                                            <ArrowRight className="w-4 h-4 text-[#ec3713]" />
                                            <span className="font-bold text-slate-300">{loc.varis_yeri}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-baseline gap-1">
                                            <span className="text-base font-black text-white">{loc.mesafe_km}</span>
                                            <span className="text-xs font-bold text-[#c99b92]">KM</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={cn(
                                            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
                                            difficulty.bg
                                        )}>
                                            {difficulty.label}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col gap-1.5">
                                            <div className="flex items-center gap-4">
                                                <div className="flex gap-2 text-xs font-bold text-[#c99b92] uppercase">
                                                    <span className="text-emerald-400">↑ {loc.ascent_m || 0}m</span>
                                                    <span className="text-red-400">↓ {loc.descent_m || 0}m</span>
                                                </div>
                                            </div>
                                            <div className={cn(
                                                "w-fit flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase",
                                                source.bg
                                            )}>
                                                {source.icon}
                                                {source.label}
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                onClick={() => onAnalyze(loc)}
                                                className="h-8 bg-[#221411] border-[#482923] text-blue-400 hover:text-white hover:bg-blue-500/20 shadow-sm flex items-center gap-1 px-2"
                                                title="Sanal Sefer Simülasyonu"
                                            >
                                                <TrendingUp className="w-3.5 h-3.5" />
                                                <span>Simüle Et</span>
                                            </Button>
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                onClick={() => onEdit(loc)}
                                                className="h-8 w-8 p-0 bg-[#221411] border-[#482923] text-amber-500 hover:text-white hover:bg-amber-500/20"
                                            >
                                                <Edit2 className="w-4 h-4" />
                                            </Button>
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                onClick={() => onDelete(loc)}
                                                className="h-8 w-8 p-0 bg-[#221411] border-[#482923] text-red-500 hover:text-white hover:bg-red-500/20"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
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
