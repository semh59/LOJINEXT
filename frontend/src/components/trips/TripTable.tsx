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
    hasActiveFilter?: boolean;
    onClearFilters?: () => void;
}

const getStatusStyles = (status?: string) => {
    switch (status) {
        case 'Tamamlandı':
        case 'Tamam':
        case 'TAMAMLANDI':
            return {
                bg: 'bg-success/10',
                text: 'text-success',
                border: 'border-success/20',
                bar: 'bg-success',
                glow: 'shadow-success/20',
                icon: <CheckCircle2 className="w-3 h-3 mr-1" />
            };
        case 'Devam Ediyor':
        case 'DEVAM_EDIYOR':
            return {
                bg: 'bg-accent/10',
                text: 'text-accent',
                border: 'border-accent/20',
                bar: 'bg-accent',
                glow: 'shadow-accent/20',
                icon: <Navigation className="w-3 h-3 mr-1" />
            };
        case 'Planlandı':
        case 'Planlanan':
        case 'Bekliyor':
            return {
                bg: 'bg-warning/10',
                text: 'text-warning',
                border: 'border-warning/20',
                bar: 'bg-warning',
                glow: '',
                icon: <Timer className="w-3 h-3 mr-1" />
            };
        case 'İptal':
        case 'IPTAL':
            return {
                bg: 'bg-danger/10',
                text: 'text-danger',
                border: 'border-danger/20',
                bar: 'bg-danger',
                glow: '',
                icon: <XCircle className="w-3 h-3 mr-1" />
            };
        default:
            return {
                bg: 'bg-bg-elevated',
                text: 'text-secondary',
                border: 'border-border',
                bar: 'bg-secondary',
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
                color: 'text-success', 
                bg: 'bg-success/20', 
                bar: 'bg-success',
                border: 'border-success/30', 
                glow: 'shadow-sm',
                text: 'Tamamlandı', 
                progress: 100 
            };
        case 'Devam Ediyor':
        case 'DEVAM_EDIYOR':
            return { 
                color: 'text-accent', 
                bg: 'bg-accent/20', 
                bar: 'bg-accent',
                border: 'border-accent/30', 
                glow: 'shadow-accent/40',
                text: 'Yolda', 
                progress: 65 
            };
        case 'Planlandı':
        case 'Planlanan':
        case 'Bekliyor':
            return { 
                color: 'text-warning', 
                bg: 'bg-warning/20', 
                bar: 'bg-warning',
                border: 'border-warning/30', 
                glow: 'shadow-sm',
                text: 'Yükleniyor', 
                progress: 5 
            };
        case 'İptal':
        case 'IPTAL':
            return { 
                color: 'text-danger', 
                bg: 'bg-danger/20', 
                bar: 'bg-danger',
                border: 'border-danger/30', 
                glow: '',
                text: 'İptal Edildi', 
                progress: 0 
            };
        default:
            return { 
                color: 'text-secondary', 
                bg: 'bg-bg-elevated', 
                bar: 'bg-secondary',
                border: 'border-border',
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
    onViewDetails,
    hasActiveFilter = false,
    onClearFilters
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
                    <div key={i} className="h-32 w-full bg-bg-elevated/50 animate-pulse rounded-[16px] border border-border" />
                ))}
            </div>
        );
    }

    if (trips.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-32 rounded-[16px] border border-dashed border-border bg-bg-elevated group">
                <div className="relative mb-6">
                    <PackageOpen className="w-16 h-16 text-secondary relative z-10 group-hover:scale-110 transition-transform duration-500" />
                </div>
                <h3 className="text-xl font-bold text-primary tracking-tight mb-2">
                    {hasActiveFilter ? 'Filtrelere Uygun Sefer Bulunamadı' : 'Henüz Sefer Bulunmuyor'}
                </h3>
                <p className="text-secondary font-medium">
                    {hasActiveFilter 
                        ? 'Farklı bir filtre deneyin veya filtreleri temizleyin.' 
                        : 'Yeni bir sefer girişi yaparak operasyonu başlatın.'}
                </p>
                {hasActiveFilter && onClearFilters && (
                    <button
                        onClick={onClearFilters}
                        className="mt-6 px-6 py-2.5 bg-bg-elevated hover:bg-surface border border-border text-primary rounded-[8px] font-bold text-sm transition-all"
                    >
                        Filtreleri Temizle
                    </button>
                )}
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
                                    "h-full group bg-surface border border-border rounded-[16px] transition-all duration-300 cursor-pointer overflow-hidden flex shadow-sm",
                                    isSelected 
                                        ? "border-accent ring-1 ring-accent/30 bg-accent/5" 
                                        : "hover:bg-bg-elevated hover:shadow"
                                )}
                            >
                                {/* Selection Indicator */}
                                <div className={cn(
                                    "w-1.5 h-full transition-all duration-500",
                                    isSelected ? "bg-accent" : statusStyles.bar
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
                                                "w-5 h-5 rounded-[6px] border-[1.5px] transition-all flex items-center justify-center",
                                                isSelected 
                                                    ? "bg-accent border-accent text-bg-base" 
                                                    : "border-border hover:border-accent/40 bg-surface"
                                            )}
                                        >
                                            {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                                        </button>
                                    </div>

                                    {/* Trip Detail Summary */}
                                    <div className="col-span-12 lg:col-span-3">
                                        <div className="flex items-center gap-3 mb-2">
                                            <div className="p-2 rounded-xl bg-bg-elevated border border-border group-hover:bg-accent/10 group-hover:border-accent/20 transition-colors">
                                                <Route className="w-4 h-4 text-secondary group-hover:text-accent transition-colors" />
                                            </div>
                                            <div>
                                                <h4 className="text-[14px] font-bold text-primary tracking-tight leading-tight group-hover:text-accent transition-colors">{trip.cikis_yeri} → {trip.varis_yeri}</h4>
                                                <p className="text-[11px] font-bold text-secondary uppercase tracking-widest leading-none mt-1">{trip.tarih} • {trip.saat}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className="px-2 py-0.5 rounded-md bg-bg-elevated border border-border text-[11px] font-bold text-secondary">ID: {trip.id}</span>
                                            {trip.sefer_no && <span className="px-2 py-0.5 rounded-md bg-accent/10 border border-accent/20 text-[11px] font-bold text-accent">{trip.sefer_no}</span>}
                                        </div>
                                    </div>

                                    {/* Vehicle & Driver */}
                                    <div className="col-span-12 md:col-span-6 lg:col-span-4 grid grid-cols-2 gap-4 border-l border-border pl-6">
                                        <div className="space-y-1">
                                            <label className="text-[11px] font-bold text-secondary uppercase tracking-widest">Araç & Dorse</label>
                                            <div className="text-[14px] font-bold text-primary">{trip.arac?.plaka || trip.arac_plaka || trip.plaka || 'Tanımsız'}</div>
                                            {(trip.dorse || trip.dorse_id) && (
                                                <div className="text-[12px] font-medium text-secondary">
                                                    {trip.dorse?.plaka || `Dorse ID: ${trip.dorse_id}`}
                                                </div>
                                            )}
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-[11px] font-bold text-secondary uppercase tracking-widest">Sürücü</label>
                                            <div className="text-[14px] font-bold text-primary flex items-center gap-2">
                                                {trip.sofor?.ad_soyad || trip.sofor_ad_soyad || trip.sofor_adi || 'Tanımsız'}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Stats & Progress */}
                                    <div className="col-span-12 md:col-span-4 lg:col-span-3 border-l border-border pl-6">
                                        <div className="flex justify-between items-center mb-2">
                                            <span className={cn(
                                                "px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider flex items-center border",
                                                statusStyles.bg, statusStyles.text, statusStyles.border
                                            )}>
                                                {statusStyles.icon}
                                                {statusConfig.text}
                                            </span>
                                            <span className="text-[12px] font-bold text-secondary tabular-nums">{statusConfig.progress}%</span>
                                        </div>
                                        <div className="w-full h-1.5 bg-bg-elevated rounded-full overflow-hidden border border-border/50">
                                            <motion.div 
                                                initial={{ width: 0 }}
                                                animate={{ width: `${statusConfig.progress}%` }}
                                                className={cn("h-full", statusConfig.bar)}
                                                transition={{ duration: 0.8, ease: "easeOut" }}
                                            />
                                        </div>
                                    </div>

                                    {/* Quick Actions */}
                                    {!isSelected && (
                                        <div className="col-span-12 lg:col-span-1 flex items-center justify-end gap-2 relative z-20">
                                            <button 
                                                onClick={(e) => { e.stopPropagation(); onEdit(trip); }}
                                                className="p-2 rounded-[8px] bg-surface border border-border hover:bg-bg-elevated hover:text-accent text-secondary transition-colors"
                                                title="Güncelle"
                                            >
                                                <Edit2 className="w-[18px] h-[18px]" />
                                            </button>

                                            <button 
                                                onClick={(e) => { e.stopPropagation(); onDelete(trip); }}
                                                className="p-2 rounded-[8px] bg-surface border border-border hover:bg-danger/10 hover:border-danger/30 text-secondary hover:text-danger transition-colors"
                                                title="Seferi Sil"
                                            >
                                                <Trash2 className="w-[18px] h-[18px]" />
                                            </button>

                                            <div className="relative group/menu">
                                                <button className="p-2 rounded-[8px] bg-surface border border-border hover:bg-bg-elevated hover:text-primary text-secondary transition-colors">
                                                    <MoreVertical className="w-[18px] h-[18px]" />
                                                </button>
                                                
                                                <div className="absolute right-0 top-full mt-2 w-56 p-2 bg-surface border border-border rounded-[16px] shadow-lg opacity-0 scale-95 pointer-events-none group-hover/menu:opacity-100 group-hover/menu:pointer-events-auto group-hover/menu:scale-100 transition-all duration-200 z-[9999] origin-top-right">
                                                    {onCreateReturn && (
                                                        <button 
                                                            onClick={(e) => { e.stopPropagation(); onCreateReturn(trip); }}
                                                            className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold tracking-tight text-secondary hover:bg-bg-elevated hover:text-accent rounded-[12px] transition-all group/item"
                                                        >
                                                            <div className="w-8 h-8 rounded-[8px] bg-bg-elevated flex items-center justify-center group-hover/item:bg-accent/10 group-hover/item:text-accent transition-colors">
                                                                <RefreshCw className="w-4 h-4" />
                                                            </div>
                                                            Dönüş Seferi Dönüştür
                                                        </button>
                                                    )}
                                                    
                                                    {onStatusChange && (
                                                        <button 
                                                            onClick={(e) => { e.stopPropagation(); onStatusChange(trip); }}
                                                            className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold tracking-tight text-secondary hover:bg-bg-elevated hover:text-primary rounded-[12px] transition-all group/item"
                                                        >
                                                            <div className="w-8 h-8 rounded-[8px] bg-bg-elevated flex items-center justify-center group-hover/item:bg-surface transition-colors">
                                                                <Settings className="w-4 h-4" />
                                                            </div>
                                                            Durum Güncelle
                                                        </button>
                                                    )}

                                                    <div className="h-px bg-border my-2 mx-1"></div>

                                                    <button 
                                                        onClick={(e) => { e.stopPropagation(); onDelete(trip); }}
                                                        className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold tracking-tight text-danger hover:bg-danger/10 rounded-[12px] transition-all"
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
