import React from 'react';
import { SeferTimelineItem } from '../../types';
import { format } from 'date-fns';
import { tr } from 'date-fns/locale';
import {
    Activity,
    Clock,
    FileEdit,
    Gauge,
    PlusCircle,
    RefreshCw,
    Trash2,
    User,
} from 'lucide-react';

interface TripTimelineProps {
    items: SeferTimelineItem[];
    isLoading?: boolean;
}

const EVENT_LABELS: Record<SeferTimelineItem['tip'], string> = {
    CREATE: 'Olusturma',
    UPDATE: 'Guncelleme',
    STATUS_CHANGE: 'Durum Gecisi',
    PREDICTION_REFRESH: 'Tahmin Yenileme',
    RECONCILIATION: 'Uzlastirma',
    DELETE: 'Silme',
};

const getEventIcon = (tip: SeferTimelineItem['tip']) => {
    switch (tip) {
        case 'CREATE':
            return <PlusCircle className="w-4 h-4 text-success" />;
        case 'DELETE':
            return <Trash2 className="w-4 h-4 text-danger" />;
        case 'STATUS_CHANGE':
            return <Activity className="w-4 h-4 text-warning" />;
        case 'PREDICTION_REFRESH':
            return <Gauge className="w-4 h-4 text-accent" />;
        case 'RECONCILIATION':
            return <RefreshCw className="w-4 h-4 text-accent" />;
        default:
            return <FileEdit className="w-4 h-4 text-secondary" />;
    }
};

const renderValue = (value: any) => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
};

export const TripTimeline: React.FC<TripTimelineProps> = ({ items, isLoading }) => {
    if (isLoading) {
        return (
            <div className="flex flex-col gap-6 py-4">
                {[...Array(3)].map((_, i) => (
                    <div key={i} className="flex gap-4 animate-pulse">
                        <div className="w-8 h-8 rounded-full bg-bg-elevated/5" />
                        <div className="flex-1 space-y-2">
                            <div className="h-4 w-1/3 bg-bg-elevated/10 rounded" />
                            <div className="h-3 w-2/3 bg-bg-elevated/5 rounded" />
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    if (!items?.length) {
        return (
            <div className="text-center py-10 text-secondary">
                <Clock className="w-10 h-10 mx-auto mb-3 opacity-20" />
                <p className="text-sm font-medium">Henuz operasyon kaydi bulunmuyor.</p>
            </div>
        );
    }

    return (
        <div className="relative space-y-8 before:absolute before:inset-0 before:ml-4 before:-translate-x-px before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-border before:to-transparent">
            {items.map((item) => (
                <div key={item.id} className="relative flex items-start gap-4 group">
                    <div className="relative flex items-center justify-center w-8 h-8 rounded-full bg-surface border border-border z-10 shadow-xl group-hover:border-accent/50 transition-colors">
                        {getEventIcon(item.tip)}
                    </div>

                    <div className="flex-1 flex flex-col gap-2 min-w-0">
                        <div className="flex items-center justify-between gap-4">
                            <span className="text-xs font-black text-primary uppercase tracking-tight truncate">
                                {EVENT_LABELS[item.tip]}
                            </span>
                            <span className="text-[10px] font-bold text-secondary whitespace-nowrap">
                                {format(new Date(item.zaman), 'HH:mm (d MMM yyyy)', { locale: tr })}
                            </span>
                        </div>

                        <p className="text-xs font-medium text-secondary leading-relaxed">
                            {item.ozet}
                        </p>

                        <div className="flex items-center gap-2 mt-1">
                            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-bg-elevated/5 border border-border">
                                <User className="w-3 h-3 text-secondary" />
                                <span className="text-[10px] font-bold text-secondary">{item.kullanici}</span>
                            </div>

                            {(item.changes?.length ?? 0) > 0 && (
                                <div className="flex flex-wrap gap-1">
                                    {(item.changes || []).slice(0, 4).map((change: any) => (
                                        <span
                                            key={`${item.id}-${change.alan}`}
                                            className="text-[9px] px-1.5 py-0.5 rounded bg-accent/10 text-accent font-bold uppercase"
                                        >
                                            {change.alan}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>

                        {(item.prediction || item.technical_details || (item.changes?.length ?? 0) > 0) && (
                            <details className="mt-2 group/details">
                                <summary className="cursor-pointer text-[10px] font-bold uppercase tracking-wider text-secondary hover:text-primary">
                                    Teknik Detaylar
                                </summary>
                                <div className="mt-2 p-3 rounded-xl border border-border bg-bg-elevated/20 space-y-3">
                                    {item.prediction && (
                                        <div className="space-y-1">
                                            <div className="text-[10px] uppercase tracking-wider text-accent font-black">
                                                Tahmin Bilgisi
                                            </div>
                                            <div className="text-[11px] text-secondary">
                                                {item.prediction.onceki_tahmini_tuketim ?? '-'} {' -> '} {item.prediction.tahmini_tuketim ?? '-'} L/100km
                                            </div>
                                            {item.prediction.tahmin_meta && (
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                                                    <div className="text-secondary">
                                                        Model: <span className="text-primary">{item.prediction.tahmin_meta.model_used ?? '-'}</span>
                                                    </div>
                                                    <div className="text-secondary">
                                                        Versiyon: <span className="text-primary">{item.prediction.tahmin_meta.model_version ?? '-'}</span>
                                                    </div>
                                                    <div className="text-secondary">
                                                        Guven: <span className="text-primary">{item.prediction.tahmin_meta.confidence_score ?? '-'}</span>
                                                    </div>
                                                    <div className="text-secondary">
                                                        Fallback: <span className="text-primary">{item.prediction.tahmin_meta.fallback_triggered ? 'Evet' : 'Hayir'}</span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {(item.changes?.length ?? 0) > 0 && (
                                        <div className="space-y-1">
                                            <div className="text-[10px] uppercase tracking-wider text-accent font-black">
                                                Alan Degisimleri
                                            </div>
                                            <div className="max-h-40 overflow-y-auto custom-scrollbar space-y-1">
                                                {(item.changes || []).map((change: any, idx: number) => (
                                                    <div key={`${item.id}-change-${idx}`} className="text-[11px] text-secondary">
                                                        <span className="text-primary font-semibold">{change.alan}:</span>{' '}
                                                        {renderValue(change.eski)} {' -> '} {renderValue(change.yeni)}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </details>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
};
