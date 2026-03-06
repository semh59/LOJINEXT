import { useRef } from 'react';
import { motion } from 'framer-motion';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Trip } from '../../types';
import { 
    Edit2, Trash2, MoreVertical, RefreshCw, XCircle, Settings, Check, Route,
    CheckCircle2, Timer, Navigation, PackageOpen, Clock
} from 'lucide-react';
import { cn } from '../../lib/utils';

export interface TripTableProps {
    trips: Trip[];
    isLoading: boolean;
    onEdit: (trip: Trip) => void;
    onDelete: (trip: Trip) => void;
    onCreateReturn?: (trip: Trip) => void;
    onStatusChange?: (trip: Trip) => void;
    selectedIds?: number[];
    onToggleSelection?: (id: number) => void;
    onViewDetails?: (trip: Trip) => void;
}

const getStatusStyles = (status?: string) => {
    switch (status) {
        case 'Tamamlandı':
        case 'Tamam':
        case 'TAMAMLANDI':
            return {
                bg: 'bg-emerald-500/10',
                text: 'text-emerald-400',
                border: 'border-emerald-500/20',
                bar: 'bg-[#10b981]',
                glow: 'shadow-[0_0_15px_rgba(16,185,129,0.3)]',
                icon: <CheckCircle2 className="w-3 h-3 mr-1" />
            };
        case 'Devam Ediyor':
        case 'DEVAM_EDIYOR':
            return {
                bg: 'bg-blue-500/10',
                text: 'text-blue-400',
                border: 'border-blue-500/20',
                bar: 'bg-gradient-to-r from-[#25d1f4] to-blue-500',
                glow: 'shadow-[0_0_15px_rgba(59,130,246,0.3)]',
                icon: <Navigation className="w-3 h-3 mr-1" />
            };
        case 'Planlandı':
        case 'Planlanan':
        case 'Bekliyor':
            return {
                bg: 'bg-amber-500/10',
                text: 'text-amber-400',
                border: 'border-amber-500/20',
                bar: 'bg-gradient-to-r from-[#f59e0b] to-orange-500',
                glow: '',
                icon: <Timer className="w-3 h-3 mr-1" />
            };
        case 'İptal':
        case 'IPTAL':
            return {
                bg: 'bg-rose-500/10',
                text: 'text-rose-400',
                border: 'border-rose-500/20',
                bar: 'bg-[#ef4444]',
                glow: '',
                icon: <XCircle className="w-3 h-3 mr-1" />
            };
        default:
            return {
                bg: 'bg-slate-500/10',
                text: 'text-slate-400',
                border: 'border-slate-500/20',
                bar: 'bg-slate-400',
                glow: '',
                icon: <Clock className="w-3 h-3 mr-1" />
            };
    }
};

const getStatusConfig = (durum?: string) => {
    switch (durum) {
        case 'Tamamlandı':
        case 'Tamam':
        case 'TAMAMLANDI':
            return { 
                color: 'text-[#10b981]', 
                bg: 'bg-[#10b981]/20', 
                bar: 'bg-[#10b981]',
                border: 'border-[#10b981]/30', 
                glow: 'shadow-[0_0_15px_rgba(16,185,129,0.2)]',
                text: 'Tamamlandı', 
                progress: 100 
            };
        case 'Devam Ediyor':
        case 'DEVAM_EDIYOR':
            return { 
                color: 'text-[#25d1f4]', 
                bg: 'bg-[#25d1f4]/20', 
                bar: 'bg-gradient-to-r from-[#25d1f4] to-blue-500',
                border: 'border-[#25d1f4]/50', 
                glow: 'shadow-[0_0_20px_rgba(37,209,244,0.4)]',
                text: 'Yolda', 
                progress: 65 
            };
        case 'Planlandı':
        case 'Planlanan':
        case 'Bekliyor':
            return { 
                color: 'text-[#f59e0b]', 
                bg: 'bg-[#f59e0b]/20', 
                bar: 'bg-gradient-to-r from-[#f59e0b] to-orange-500',
                border: 'border-[#f59e0b]/30', 
                glow: 'shadow-[0_0_15px_rgba(245,158,11,0.2)]',
                text: 'Yükleniyor', 
                progress: 5 
            };
        case 'İptal':
        case 'IPTAL':
            return { 
                color: 'text-[#ef4444]', 
                bg: 'bg-[#ef4444]/20', 
                bar: 'bg-[#ef4444]',
                border: 'border-[#ef4444]/30', 
                glow: '',
                text: 'İptal Edildi', 
                progress: 0 
            };
        default:
            return { 
                color: 'text-slate-400', 
                bg: 'bg-slate-400/20', 
                bar: 'bg-slate-500',
                border: 'border-white/10',
                glow: '',
                text: durum || 'Belirsiz',
                progress: 0
            };
    }
};

export function TripTable({ 
    trips, 
    isLoading, 
    onEdit, 
    onDelete, 
    onCreateReturn, 
    onStatusChange,
    selectedIds = [],
    onToggleSelection,
    onViewDetails
}: TripTableProps) {
    const parentRef = useRef<HTMLDivElement>(null);

    const rowVirtualizer = useVirtualizer({
        count: trips.length,
        getScrollElement: () => parentRef.current,
        estimateSize: () => 140,
        overscan: 5
    });

    if (isLoading) {
        return (
            <div className="flex flex-col gap-4 mt-8">
                {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="h-32 w-full bg-white/5 animate-pulse rounded-2xl border border-white/5" />
                ))}
            </div>
        );
    }

    if (trips.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-32 rounded-[32px] border-2 border-dashed border-white/5 bg-[#132326]/30 group">
                <div className="relative mb-6">
                    <div className="absolute inset-0 bg-[#25d1f4]/20 blur-3xl rounded-full scale-150 animate-pulse"></div>
                    <PackageOpen className="w-16 h-16 text-[#25d1f4]/40 relative z-10 group-hover:scale-110 transition-transform duration-500" />
                </div>
                <h3 className="text-xl font-black text-white uppercase tracking-tight mb-2">Henüz Sefer Bulunmuyor</h3>
                <p className="text-slate-500 font-medium">Yeni bir sefer girişi yaparak operasyonu başlatın.</p>
            </div>
        );
    }

    return (
        <div ref={parentRef} className="mt-8 overflow-y-auto custom-scrollbar" style={{ maxHeight: 'calc(100vh - 420px)' }}>
            <div
                style={{
                    height: `${rowVirtualizer.getTotalSize()}px`,
                    width: '100%',
                    position: 'relative',
                }}
            >
                {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                    const trip = trips[virtualRow.index];
                    const isSelected = selectedIds.includes(trip.id!);
                    const statusConfig = getStatusConfig(trip.durum);
                    const statusStyles = getStatusStyles(trip.durum);

                    return (
                        <div
                            key={virtualRow.key}
                            style={{
                                position: 'absolute',
                                top: 0,
                                left: 0,
                                width: '100%',
                                height: `${virtualRow.size}px`,
                                transform: `translateY(${virtualRow.start}px)`,
                                paddingBottom: '16px'
                            }}
                        >
                            <div 
                                onClick={() => onViewDetails?.(trip)}
                                className={cn(
                                    "h-full group bg-[#132326]/60 backdrop-blur-md border rounded-2xl transition-all duration-300 cursor-pointer overflow-hidden flex",
                                    isSelected 
                                        ? "border-[#25d1f4]/50 shadow-[0_0_30px_rgba(37,209,244,0.15)] ring-1 ring-[#25d1f4]/30" 
                                        : "border-white/5 hover:border-white/20 hover:bg-[#1a2d30]/80 shadow-xl"
                                )}
                            >
                                {/* Selection Indicator */}
                                <div className={cn(
                                    "w-1.5 h-full transition-all duration-500",
                                    isSelected ? "bg-[#25d1f4]" : statusStyles.bar
                                )} />

                                <div className="flex-1 p-5 lg:p-6 grid grid-cols-12 gap-4 lg:gap-6 items-center">
                                    {/* Checkbox */}
                                    <div className="col-span-12 lg:col-span-1 flex items-center justify-center lg:justify-start">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onToggleSelection?.(trip.id!);
                                            }}
                                            className={cn(
                                                "w-6 h-6 rounded-lg border-2 transition-all flex items-center justify-center",
                                                isSelected 
                                                    ? "bg-[#25d1f4] border-[#25d1f4] shadow-[0_0_10px_rgba(37,209,244,0.4)]" 
                                                    : "border-white/10 hover:border-white/30 bg-white/5"
                                            )}
                                        >
                                            {isSelected && <Check className="w-4 h-4 text-[#0B1215] stroke-[4]" />}
                                        </button>
                                    </div>

                                    {/* Trip Detail Summary */}
                                    <div className="col-span-12 lg:col-span-3">
                                        <div className="flex items-center gap-3 mb-2">
                                            <div className="p-2 rounded-xl bg-white/5 border border-white/10 group-hover:bg-[#25d1f4]/10 group-hover:border-[#25d1f4]/20 transition-colors">
                                                <Route className="w-4 h-4 text-[#25d1f4]" />
                                            </div>
                                            <div>
                                                <h4 className="text-sm font-black text-white group-hover:text-[#25d1f4] transition-colors">{trip.cikis_yeri} → {trip.varis_yeri}</h4>
                                                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest leading-none mt-1">{trip.tarih} • {trip.saat}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[10px] font-bold text-slate-400">ID: {trip.id}</span>
                                            {trip.sefer_no && <span className="px-2 py-0.5 rounded-md bg-[#25d1f4]/10 border border-[#25d1f4]/20 text-[10px] font-bold text-[#25d1f4]">{trip.sefer_no}</span>}
                                        </div>
                                    </div>

                                    {/* Vehicle & Driver */}
                                    <div className="col-span-12 md:col-span-6 lg:col-span-4 grid grid-cols-2 gap-4 border-l border-white/5 pl-6">
                                        <div className="space-y-1">
                                            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Araç & Dorse</label>
                                            <div className="text-sm font-bold text-slate-200">{trip.arac?.plaka || trip.arac_plaka || trip.plaka || 'Tanımsız'}</div>
                                            {(trip.dorse || trip.dorse_id) && (
                                                <div className="text-[11px] font-medium text-slate-400">
                                                    {trip.dorse?.plaka || `Dorse ID: ${trip.dorse_id}`}
                                                </div>
                                            )}
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Sürücü</label>
                                            <div className="text-sm font-bold text-slate-200 flex items-center gap-2">
                                                {trip.sofor?.ad_soyad || trip.sofor_ad_soyad || trip.sofor_adi || 'Tanımsız'}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Stats & Progress */}
                                    <div className="col-span-12 md:col-span-4 lg:col-span-3 border-l border-white/5 pl-6">
                                        <div className="flex justify-between items-center mb-2">
                                            <span className={cn(
                                                "px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider flex items-center border",
                                                statusStyles.bg, statusStyles.text, statusStyles.border
                                            )}>
                                                {statusStyles.icon}
                                                {statusConfig.text}
                                            </span>
                                            <span className="text-[10px] font-bold text-slate-500">{statusConfig.progress}%</span>
                                        </div>
                                        <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                                            <motion.div 
                                                initial={{ width: 0 }}
                                                animate={{ width: `${statusConfig.progress}%` }}
                                                className={cn("h-full", statusConfig.bar)}
                                            />
                                        </div>
                                    </div>

                                    {/* Quick Actions */}
                                    {!isSelected && (
                                        <div className="col-span-12 lg:col-span-1 flex items-center justify-end gap-2">
                                            <button 
                                                onClick={(e) => { e.stopPropagation(); onEdit(trip); }}
                                                className="p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-[#25d1f4]/20 hover:border-[#25d1f4]/40 text-[#25d1f4] transition-all shadow-lg group/edit"
                                                title="Güncelle"
                                            >
                                                <Edit2 className="w-4 h-4" />
                                            </button>

                                            <button 
                                                onClick={(e) => { e.stopPropagation(); onDelete(trip); }}
                                                className="p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-rose-500/20 hover:border-rose-500/40 text-rose-400 hover:text-rose-500 transition-all shadow-lg group/delete"
                                                title="Seferi Sil"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>

                                            <div className="relative group/menu">
                                                <button className="p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/20 hover:border-white/30 text-white transition-all shadow-lg hover:shadow-[0_0_15px_rgba(255,255,255,0.2)]">
                                                    <MoreVertical className="w-4 h-4" />
                                                </button>
                                                
                                                <div className="absolute right-0 top-full mt-2 w-56 p-2 bg-[#0B1215] border border-white/20 rounded-2xl shadow-[0_20px_60px_-10px_rgba(37,209,244,0.3)] opacity-0 scale-95 pointer-events-none group-hover/menu:opacity-100 group-hover/menu:pointer-events-auto group-hover/menu:scale-100 transition-all duration-200 z-[9999] origin-top-right">
                                                    {onCreateReturn && (
                                                        <button 
                                                            onClick={(e) => { e.stopPropagation(); onCreateReturn(trip); }}
                                                            className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold tracking-tight text-slate-200 hover:bg-[#25d1f4]/10 hover:text-[#25d1f4] rounded-xl transition-all group/item"
                                                        >
                                                            <div className="w-8 h-8 rounded-lg bg-[#25d1f4]/10 flex items-center justify-center group-hover/item:bg-[#25d1f4]/20 transition-colors">
                                                                <RefreshCw className="w-4 h-4" />
                                                            </div>
                                                            Dönüş Seferi Dönüştür
                                                        </button>
                                                    )}
                                                    
                                                    {onStatusChange && (
                                                        <button 
                                                            onClick={(e) => { e.stopPropagation(); onStatusChange(trip); }}
                                                            className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold tracking-tight text-slate-200 hover:bg-white/10 rounded-xl transition-all group/item"
                                                        >
                                                            <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center group-hover/item:bg-white/15 transition-colors">
                                                                <Settings className="w-4 h-4" />
                                                            </div>
                                                            Durum Güncelle
                                                        </button>
                                                    )}

                                                    <div className="h-px bg-white/10 my-2 mx-1"></div>

                                                    <button 
                                                        onClick={(e) => { e.stopPropagation(); onDelete(trip); }}
                                                        className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold tracking-tight text-rose-500 hover:bg-rose-500 hover:text-white rounded-xl transition-all"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                        Seferi Sil
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
