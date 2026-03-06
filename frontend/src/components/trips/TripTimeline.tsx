import React from 'react';
import { SeferTimelineItem } from '../../types';
import { format } from 'date-fns';
import { tr } from 'date-fns/locale';
import { 
    Clock, 
    User, 
    Activity, 
    FileEdit,
    PlusCircle,
    Trash2
} from 'lucide-react';

interface TripTimelineProps {
    items: SeferTimelineItem[];
    isLoading?: boolean;
}

const getActionIcon = (aksiyon: string) => {
    const a = aksiyon.toLowerCase();
    if (a.includes('create') || a.includes('ekle')) return <PlusCircle className="w-4 h-4 text-emerald-500" />;
    if (a.includes('update') || a.includes('güncelle')) return <FileEdit className="w-4 h-4 text-blue-500" />;
    if (a.includes('delete') || a.includes('sil')) return <Trash2 className="w-4 h-4 text-rose-500" />;
    if (a.includes('status') || a.includes('durum')) return <Activity className="w-4 h-4 text-amber-500" />;
    return <Clock className="w-4 h-4 text-slate-400" />;
};

export const TripTimeline: React.FC<TripTimelineProps> = ({ items, isLoading }) => {
    if (isLoading) {
        return (
            <div className="flex flex-col gap-6 py-4">
                {[...Array(3)].map((_, i) => (
                    <div key={i} className="flex gap-4 animate-pulse">
                        <div className="w-8 h-8 rounded-full bg-white/5" />
                        <div className="flex-1 space-y-2">
                            <div className="h-4 w-1/4 bg-white/5 rounded" />
                            <div className="h-3 w-3/4 bg-white/5 rounded" />
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    if (!items?.length) {
        return (
            <div className="text-center py-10 text-slate-500">
                <Clock className="w-10 h-10 mx-auto mb-3 opacity-20" />
                <p className="text-sm font-medium">Henüz bir olay kaydı bulunmuyor.</p>
            </div>
        );
    }

    return (
        <div className="relative space-y-8 before:absolute before:inset-0 before:ml-4 before:-translate-x-px before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-white/5 before:to-transparent">
            {items.map((item) => (
                <div key={item.id} className="relative flex items-start gap-4 group">
                    <div className="relative flex items-center justify-center w-8 h-8 rounded-full bg-[#131c20] border border-white/10 z-10 shadow-xl group-hover:border-[#25d1f4]/50 transition-colors">
                        {getActionIcon(item.aksiyon)}
                    </div>

                    <div className="flex-1 flex flex-col gap-1 min-w-0">
                        <div className="flex items-center justify-between gap-4">
                            <span className="text-xs font-black text-white uppercase tracking-tight truncate">
                                {item.aksiyon}
                            </span>
                            <span className="text-[10px] font-bold text-slate-500 whitespace-nowrap">
                                {format(new Date(item.zaman), 'HH:mm (d MMM yyyy)', { locale: tr })}
                            </span>
                        </div>
                        
                        {item.aciklama && (
                            <p className="text-xs font-medium text-slate-400 leading-relaxed">
                                {item.aciklama}
                            </p>
                        )}

                        <div className="flex items-center gap-2 mt-1">
                            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-white/5 border border-white/5">
                                <User className="w-3 h-3 text-slate-500" />
                                <span className="text-[10px] font-bold text-slate-400">{item.kullanici}</span>
                            </div>
                            
                            {item.degisen_alanlar?.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                    {item.degisen_alanlar.map((field) => (
                                        <span key={field} className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 font-bold uppercase">
                                            {field}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};
