import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    MoreVertical,
    Truck,
    User,
    ArrowRight,
    CheckCircle2,
    Clock,
    XCircle,
    MapPin,
    Navigation,
    TrendingUp
} from 'lucide-react';
import { Trip } from '../../types';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '../ui/Table';
import { format, parseISO } from 'date-fns';

/**
 * Kurumsal seviyede Sefer Tablosu
 * - Staggered animasyonlar
 * - Özel durum rozetleri
 * - Detaylı güzergah görünümü
 * - Hover aksiyonları
 */

interface TripTableProps {
    trips: Trip[];
    isLoading: boolean;
    onEdit: (trip: Trip) => void;
    onDelete: (id: number) => void;
}

const STATUS_CONFIG: Record<string, { variant: "success" | "warning" | "error" | "default", icon: any, label: string }> = {
    'Tamam': { variant: 'success', icon: CheckCircle2, label: 'Tamamlandı' },
    'Devam Ediyor': { variant: 'warning', icon: Clock, label: 'Yolda' },
    'İptal': { variant: 'error', icon: XCircle, label: 'İptal' },
    'Planlandı': { variant: 'default', icon: Clock, label: 'Planlandı' },
};

export const TripTable: React.FC<TripTableProps> = ({ trips, isLoading, onEdit, onDelete }) => {

    if (isLoading) {
        return (
            <div className="bg-white rounded-[32px] border border-slate-200 overflow-hidden">
                <Table>
                    <TableHeader className="bg-slate-50/50">
                        <TableRow>
                            <TableHead className="w-[120px]">Tarih</TableHead>
                            <TableHead>Araç / Şoför</TableHead>
                            <TableHead>Güzergah</TableHead>
                            <TableHead className="text-right">Mesafe</TableHead>
                            <TableHead className="text-right">Yük</TableHead>
                            <TableHead>Durum</TableHead>
                            <TableHead className="w-[80px]"></TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {Array(6).fill(0).map((_, i) => (
                            <TableRow key={i}>
                                {Array(7).fill(0).map((_, j) => (
                                    <TableCell key={j}>
                                        <div className="h-5 bg-slate-100 rounded-lg animate-pulse w-full" />
                                    </TableCell>
                                ))}
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        );
    }

    if (trips.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-20 bg-white rounded-[32px] border border-dashed border-slate-300">
                <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                    <MapPin className="w-10 h-10 text-slate-300" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">Sefer Bulunamadı</h3>
                <p className="text-slate-500 mt-1">Belirlediğiniz kriterlere uygun kayıt bulunmuyor.</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-[32px] border border-slate-200/60 shadow-xl shadow-slate-200/20 overflow-hidden">
            <div className="overflow-x-auto">
                <Table>
                    <TableHeader className="bg-slate-50/50">
                        <TableRow className="border-b border-slate-100">
                            <TableHead className="px-6 py-4 font-bold text-slate-500 uppercase tracking-wider text-[11px]">Sefer Detayı</TableHead>
                            <TableHead className="px-6 py-4 font-bold text-slate-500 uppercase tracking-wider text-[11px]">Araç & Personel</TableHead>
                            <TableHead className="px-6 py-4 font-bold text-slate-500 uppercase tracking-wider text-[11px]">Güzergah</TableHead>
                            <TableHead className="px-6 py-4 font-bold text-slate-500 uppercase tracking-wider text-[11px] text-right">Lojistik</TableHead>
                            <TableHead className="px-6 py-4 font-bold text-slate-500 uppercase tracking-wider text-[11px]">Durum</TableHead>
                            <TableHead className="px-6 py-4 w-[60px]"></TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        <AnimatePresence mode="popLayout">
                            {trips.map((trip, idx) => {
                                const status = STATUS_CONFIG[trip.durum] || STATUS_CONFIG['Planlandı'];
                                const StatusIcon = status.icon;

                                return (
                                    <motion.tr
                                        key={trip.id || idx}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, scale: 0.95 }}
                                        transition={{ delay: idx * 0.03 }}
                                        className="group border-b border-slate-50 hover:bg-slate-50/80 transition-all cursor-pointer"
                                        onClick={() => onEdit(trip)}
                                    >
                                        {/* Tarih & Saat */}
                                        <TableCell className="px-6 py-5">
                                            <div className="flex flex-col">
                                                <span className="font-bold text-slate-900 tabular-nums">
                                                    {format(parseISO(`${trip.tarih}T00:00:00`), 'dd.MM.yyyy')}
                                                </span>
                                                <div className="flex items-center gap-1.5 text-slate-400 mt-1">
                                                    <Clock className="w-3 h-3" />
                                                    <span className="text-xs font-medium tabular-nums">{trip.saat?.slice(0, 5)}</span>
                                                </div>
                                            </div>
                                        </TableCell>

                                        {/* Araç & Şoför */}
                                        <TableCell className="px-6 py-5">
                                            <div className="flex flex-col gap-2">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-7 h-7 bg-indigo-50 rounded-lg flex items-center justify-center">
                                                        <Truck className="w-3.5 h-3.5 text-indigo-600" />
                                                    </div>
                                                    <span className="font-bold text-slate-800 text-sm tracking-tight">{trip.plaka || '34ABC123'}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <div className="w-7 h-7 bg-amber-50 rounded-lg flex items-center justify-center">
                                                        <User className="w-3.5 h-3.5 text-amber-600" />
                                                    </div>
                                                    <span className="font-medium text-slate-500 text-xs">{trip.sofor_adi || 'Bilinmeyen Şoför'}</span>
                                                </div>
                                            </div>
                                        </TableCell>

                                        {/* Güzergah */}
                                        <TableCell className="px-6 py-5">
                                            <div className="flex items-center gap-3">
                                                <div className="flex flex-col">
                                                    <span className="text-xs font-bold text-slate-400 uppercase">ÇIKIŞ</span>
                                                    <span className="font-bold text-slate-800">{trip.cikis_yeri}</span>
                                                </div>
                                                <ArrowRight className="w-4 h-4 text-slate-200 mt-4" />
                                                <div className="flex flex-col">
                                                    <span className="text-xs font-bold text-slate-400 uppercase">VARIŞ</span>
                                                    <span className="font-bold text-slate-800">{trip.varis_yeri}</span>
                                                </div>
                                            </div>
                                        </TableCell>

                                        {/* Mesafe & Yük */}
                                        <TableCell className="px-6 py-5 text-right">
                                            <div className="flex flex-col items-end gap-2">
                                                <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-50 rounded-lg border border-slate-100">
                                                    <Navigation className="w-3 h-3 text-slate-400" />
                                                    <span className="text-xs font-bold text-slate-700 tabular-nums">
                                                        {trip.mesafe_km?.toLocaleString('tr-TR')} km
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-50 rounded-lg border border-slate-100">
                                                    <TrendingUp className="w-3 h-3 text-slate-400" />
                                                    <span className="text-xs font-bold text-slate-700 tabular-nums">
                                                        {trip.ton?.toFixed(1) || (trip.net_kg / 1000).toFixed(1)} ton
                                                    </span>
                                                </div>
                                            </div>
                                        </TableCell>

                                        {/* Durum */}
                                        <TableCell className="px-6 py-5">
                                            <Badge variant={status.variant} className="rounded-xl px-3 py-1 font-bold text-[10px] uppercase tracking-wider gap-2">
                                                <StatusIcon className="w-3 h-3 shrink-0" />
                                                {status.label}
                                            </Badge>
                                        </TableCell>

                                        {/* Aksiyonlar */}
                                        <TableCell className="px-6 py-5">
                                            <div className="opacity-0 group-hover:opacity-100 transition-all flex justify-end">
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="w-9 h-9 rounded-xl text-slate-400 hover:text-indigo-600 hover:bg-indigo-50"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        onEdit(trip);
                                                    }}
                                                >
                                                    <MoreVertical className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        </TableCell>
                                    </motion.tr>
                                );
                            })}
                        </AnimatePresence>
                    </TableBody>
                </Table>
            </div>
        </div>
    );
};
