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
                bg: 'bg-danger/10 text-danger border-danger/20',
                dot: 'bg-danger'
            };
        case 'Orta':
            return {
                label: 'Eğimli',
                icon: <TrendingUp className="w-3 h-3" />,
                bg: 'bg-warning/10 text-warning border-warning/20',
                dot: 'bg-warning'
            };
        default:
            return {
                label: 'Düz',
                icon: <Wind className="w-3 h-3" />,
                bg: 'bg-success/10 text-success border-success/20',
                dot: 'bg-success'
            };
    }
};

const getSourceConfig = (source: string | undefined) => {
    switch (source?.toLowerCase()) {
        case 'mapbox_hybrid':
        case 'mapbox':
            return {
                label: 'Sistem-V2',
                bg: 'bg-info/10 text-info border-info/20',
                icon: <Database className="w-3 h-3" />
            };
        case 'api':
        case 'openrouteservice':
            return {
                label: 'Sistem-V1',
                bg: 'bg-accent/10 text-accent border-accent/20',
                icon: <Database className="w-3 h-3" />
            };
        case 'cache':
            return {
                label: 'Önbellek',
                bg: 'bg-success/10 text-success border-success/20',
                icon: <Database className="w-3 h-3" />
            };
        default:
            return {
                label: 'Sistem',
                bg: 'bg-bg-elevated text-secondary border-border',
                icon: <Database className="w-3 h-3" />
            };
    }
};

const SkeletonRow = () => (
    <tr className="animate-pulse border-b border-border">
        <td className="px-6 py-4"><div className="h-4 bg-bg-elevated/50 rounded w-24" /></td>
        <td className="px-6 py-4"><div className="h-4 bg-bg-elevated/50 rounded w-24" /></td>
        <td className="px-6 py-4"><div className="h-4 bg-bg-elevated/50 rounded w-16" /></td>
        <td className="px-6 py-4"><div className="h-4 bg-bg-elevated/50 rounded w-12" /></td>
        <td className="px-6 py-4"><div className="h-4 bg-bg-elevated/50 rounded w-20" /></td>
        <td className="px-6 py-4 text-right"><div className="h-8 bg-bg-elevated/50 rounded-lg w-20 ml-auto" /></td>
    </tr>
);

export function LocationList({ locations, loading, onEdit, onDelete, onAnalyze, onAdd }: LocationListProps) {
    if (loading) {
        return (
            <div className="bg-surface rounded-xl border border-border shadow-sm overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead className="text-secondary text-xs uppercase tracking-wider bg-bg-elevated border-b border-border">
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
            <div className="flex flex-col items-center justify-center py-20 px-4 text-center bg-surface rounded-xl border-2 border-dashed border-border">
                <div className="w-20 h-20 rounded-full bg-bg-elevated flex items-center justify-center mb-6">
                    <MapPin className="w-10 h-10 text-secondary" />
                </div>
                <h3 className="text-2xl font-bold text-primary mb-2">Güzergah Bulunamadı</h3>
                <p className="text-secondary max-w-md mb-8">
                    Arama kriterlerinize uygun güzergah bulunamadı veya henüz hiç güzergah eklenmemiş.
                </p>
                <button onClick={onAdd} className="flex items-center gap-2 bg-accent hover:bg-accent/80 text-bg-base font-bold py-2.5 px-6 rounded-lg shadow-sm transition-all">
                    <ArrowRight className="w-5 h-5" />
                    İlk Güzergahı Ekle
                </button>
            </div>
        );
    }

    return (
        <div className="bg-surface rounded-xl border border-border shadow-sm overflow-hidden flex flex-col flex-1 min-h-0">
            <div className="p-4 border-b border-border flex items-center justify-between">
                <h3 className="text-primary text-lg font-bold">Kayıtlı Güzergahlar</h3>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="text-secondary text-xs uppercase tracking-wider bg-bg-elevated border-b border-border">
                        <tr>
                            <th className="px-6 py-4 font-medium">Güzargah Bilgisi</th>
                            <th className="px-6 py-4 font-medium">Varış Noktası</th>
                            <th className="px-6 py-4 font-medium">Mesafe</th>
                            <th className="px-6 py-4 font-medium">Zorluk Seviyesi</th>
                            <th className="px-6 py-4 font-medium">Teknik Veriler</th>
                            <th className="px-6 py-4 font-medium text-right">İşlemler</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border text-sm text-primary">
                        {locations.map((loc, index) => {
                            const difficulty = getDifficultyConfig(loc.zorluk);
                            const source = getSourceConfig(loc.source);
                            return (
                                <motion.tr
                                    key={loc.id}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.03 }}
                                    className="hover:bg-bg-elevated transition-colors group"
                                >
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="size-8 rounded-lg bg-bg-elevated border border-border flex items-center justify-center text-accent">
                                                <MapPin className="w-4 h-4" />
                                            </div>
                                            <span className="font-bold text-primary tracking-wide">{loc.cikis_yeri}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2">
                                            <ArrowRight className="w-4 h-4 text-accent" />
                                            <span className="font-bold text-secondary">{loc.varis_yeri}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-baseline gap-1">
                                            <span className="text-base font-bold text-primary tabular-nums">{loc.mesafe_km}</span>
                                            <span className="text-[10px] font-bold text-secondary uppercase">KM</span>
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
                                                <div className="flex gap-2 text-xs font-bold text-secondary uppercase tabular-nums">
                                                    <span className="text-success">↑ {loc.ascent_m || 0}m</span>
                                                    <span className="text-danger">↓ {loc.descent_m || 0}m</span>
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
                                                className="h-8 bg-bg-elevated border-border text-info hover:text-bg-base hover:bg-info shadow-sm flex items-center gap-1 px-2"
                                                title="Sanal Sefer Simülasyonu"
                                            >
                                                <TrendingUp className="w-3.5 h-3.5" />
                                                <span>Simüle Et</span>
                                            </Button>
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                onClick={() => onEdit(loc)}
                                                className="h-8 w-8 p-0 bg-bg-elevated border-border text-warning hover:text-bg-base hover:bg-warning"
                                            >
                                                <Edit2 className="w-4 h-4" />
                                            </Button>
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                onClick={() => onDelete(loc)}
                                                className="h-8 w-8 p-0 bg-bg-elevated border-border text-danger hover:text-bg-base hover:bg-danger"
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
