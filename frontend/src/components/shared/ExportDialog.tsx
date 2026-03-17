import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    X, 
    FileText, 
    FileSpreadsheet, 
    Calendar, 
    Truck, 
    Download, 
    CheckCircle2,
    Loader2,
    AlertCircle
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { Button } from '../ui/Button';
import { vehiclesApi } from '../../services/api';

export type ExportType = 
    | 'fleet_summary' 
    | 'vehicle_report' 
    | 'driver_comparison' 
    | 'cost_trend' 
    | 'trip_list' 
    | 'fuel_list' 
    | 'location_list' 
    | 'driver_list'
    | 'vehicle_list';

export interface ExportConfig {
    format: 'pdf' | 'excel';
    startDate?: string;
    endDate?: string;
    targetId?: string | number; // For vehicle_report or specific driver
    month?: number;
    year?: number;
}

export interface ExportDialogProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    description: string;
    type: ExportType;
    onExport: (config: ExportConfig) => Promise<void>;
}

export function ExportDialog({
    isOpen,
    onClose,
    title,
    description,
    type,
    onExport
}: ExportDialogProps) {
    const [format, setFormat] = useState<'pdf' | 'excel'>('pdf');
    const [startDate, setStartDate] = useState(
        new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0]
    );
    const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
    const [month, setMonth] = useState(new Date().getMonth() + 1);
    const [year, setYear] = useState(new Date().getFullYear());
    const [selectedVehicleId, setSelectedVehicleId] = useState<string>('');
    const [vehicles, setVehicles] = useState<any[]>([]);
    const [isLoadingVehicles, setIsLoadingVehicles] = useState(false);
    const [isExporting, setIsExporting] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    React.useEffect(() => {
        if (isOpen && type === 'vehicle_report') {
            setIsLoadingVehicles(true);
            vehiclesApi.getAll({ limit: 100 })
                .then(data => {
                    const items = Array.isArray(data) ? data : data.items || [];
                    setVehicles(items);
                    if (items.length > 0) setSelectedVehicleId(items[0].id.toString());
                })
                .catch(err => {
                    console.error('Araçlar yüklenemedi:', err);
                    setError('Araç listesi yüklenemedi.');
                })
                .finally(() => setIsLoadingVehicles(false));
        }
    }, [isOpen, type]);

    // Disable PDF for raw data if backend doesn't support it (e.g. location_list)
    const isPdfSupported = ![
        'location_list', 
        'driver_list', 
        'vehicle_list', 
        'fuel_list', 
        'trip_list'
    ].includes(type);

    const handleExport = async () => {
        setIsExporting(true);
        setError(null);
        try {
            if (type === 'vehicle_report' && !selectedVehicleId) {
                throw new Error('Lütfen bir araç seçiniz.');
            }

            await onExport({
                format,
                startDate,
                endDate,
                targetId: selectedVehicleId,
                month,
                year
            });
            setIsSuccess(true);
            setTimeout(() => {
                setIsSuccess(false);
                onClose();
            }, 2000);
        } catch (err: any) {
            setError(err.message || 'Export işlemi başarısız oldu.');
        } finally {
            setIsExporting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
                className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            />
            
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="relative w-full max-w-lg bg-bg-elevated border border-border rounded-2xl shadow-2xl overflow-hidden"
            >
                {/* Header */}
                <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-bg-muted/30">
                    <div>
                        <h3 className="text-lg font-bold text-primary">{title}</h3>
                        <p className="text-xs text-secondary mt-0.5">{description}</p>
                    </div>
                    <button 
                        onClick={onClose}
                        className="p-2 hover:bg-bg-muted rounded-full transition-colors text-secondary hover:text-primary"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                    {/* Format Selection */}
                    <div className="space-y-3">
                        <label className="text-sm font-bold text-secondary uppercase tracking-wider">Dosya Formatı</label>
                        <div className="grid grid-cols-2 gap-4">
                            <button
                                onClick={() => isPdfSupported && setFormat('pdf')}
                                disabled={!isPdfSupported}
                                className={cn(
                                    "flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all group",
                                    format === 'pdf' 
                                        ? "border-accent bg-accent/5" 
                                        : "border-border hover:border-border-hover bg-bg-muted/50",
                                    !isPdfSupported && "opacity-50 cursor-not-allowed grayscale"
                                )}
                            >
                                <div className={cn(
                                    "p-3 rounded-lg transition-colors",
                                    format === 'pdf' ? "bg-accent text-white" : "bg-bg-elevated text-secondary group-hover:text-primary"
                                )}>
                                    <FileText className="w-6 h-6" />
                                </div>
                                <div className="text-center">
                                    <span className="block font-bold text-primary">PDF Rapor</span>
                                    <span className="text-[11px] text-secondary">Görsel & Analiz Odaklı</span>
                                </div>
                            </button>

                            <button
                                onClick={() => setFormat('excel')}
                                className={cn(
                                    "flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all group",
                                    format === 'excel' 
                                        ? "border-green-500 bg-green-500/5" 
                                        : "border-border hover:border-border-hover bg-bg-muted/50"
                                )}
                            >
                                <div className={cn(
                                    "p-3 rounded-lg transition-colors",
                                    format === 'excel' ? "bg-green-500 text-white" : "bg-bg-elevated text-secondary group-hover:text-primary"
                                )}>
                                    <FileSpreadsheet className="w-6 h-6" />
                                </div>
                                <div className="text-center">
                                    <span className="block font-bold text-primary">Excel Tablo</span>
                                    <span className="text-[11px] text-secondary">Veri & Liste Odaklı</span>
                                </div>
                            </button>
                        </div>
                    </div>

                    {/* Filters */}
                    <div className="space-y-4 pt-2">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-secondary flex items-center gap-2">
                                    <Calendar className="w-3.5 h-3.5" /> BAŞLANGIÇ
                                </label>
                                <input 
                                    type="date" 
                                    value={startDate}
                                    onChange={(e) => setStartDate(e.target.value)}
                                    className="w-full bg-bg-muted border border-border rounded-lg px-3 py-2 text-sm text-primary focus:border-accent outline-none"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-secondary flex items-center gap-2">
                                    <Calendar className="w-3.5 h-3.5" /> BİTİŞ
                                </label>
                                <input 
                                    type="date" 
                                    value={endDate}
                                    onChange={(e) => setEndDate(e.target.value)}
                                    className="w-full bg-bg-muted border border-border rounded-lg px-3 py-2 text-sm text-primary focus:border-accent outline-none"
                                />
                            </div>
                        </div>

                        {type === 'vehicle_report' && (
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-secondary flex items-center gap-2">
                                        <Truck className="w-3.5 h-3.5" /> ARAÇ SEÇİMİ
                                    </label>
                                    <select
                                        value={selectedVehicleId}
                                        onChange={(e) => setSelectedVehicleId(e.target.value)}
                                        disabled={isLoadingVehicles}
                                        className="w-full bg-bg-muted border border-border rounded-lg px-3 py-2 text-sm text-primary focus:border-accent outline-none"
                                    >
                                        {isLoadingVehicles ? (
                                            <option>Yükleniyor...</option>
                                        ) : vehicles.length === 0 ? (
                                            <option>Araç bulunamadı</option>
                                        ) : (
                                            vehicles.map(v => (
                                                <option key={v.id} value={v.id}>{v.plaka} - {v.marka} {v.model}</option>
                                            ))
                                        )}
                                    </select>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-secondary flex items-center gap-2">
                                            <Calendar className="w-3.5 h-3.5" /> AY
                                        </label>
                                        <select
                                            value={month}
                                            onChange={(e) => setMonth(Number(e.target.value))}
                                            className="w-full bg-bg-muted border border-border rounded-lg px-3 py-2 text-sm text-primary focus:border-accent outline-none"
                                        >
                                            {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                                                <option key={m} value={m}>{new Date(2000, m - 1).toLocaleString('tr', { month: 'long' })}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-secondary flex items-center gap-2">
                                            <Calendar className="w-3.5 h-3.5" /> YIL
                                        </label>
                                        <select
                                            value={year}
                                            onChange={(e) => setYear(Number(e.target.value))}
                                            className="w-full bg-bg-muted border border-border rounded-lg px-3 py-2 text-sm text-primary focus:border-accent outline-none"
                                        >
                                            {[2023, 2024, 2025, 2026].map(y => (
                                                <option key={y} value={y}>{y}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {error && (
                        <div className="flex items-center gap-3 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500 text-sm">
                            <AlertCircle className="w-5 h-5 flex-shrink-0" />
                            {error}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-bg-muted/30 border-t border-border flex items-center justify-end gap-3">
                    <Button 
                        variant="ghost" 
                        onClick={onClose}
                        disabled={isExporting}
                    >
                        Vazgeç
                    </Button>
                    <Button 
                        onClick={handleExport}
                        disabled={isExporting || isSuccess}
                        className={cn(
                            "min-w-[140px] relative transition-all overflow-hidden",
                            isSuccess && "bg-green-600 hover:bg-green-600 border-none",
                            format === 'excel' && !isSuccess && "bg-green-500 hover:bg-green-600 text-white"
                        )}
                    >
                        <AnimatePresence mode="wait">
                            {isExporting ? (
                                <motion.div 
                                    key="loading"
                                    initial={{ opacity: 0, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="flex items-center justify-center gap-2"
                                >
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>Hazırlanıyor...</span>
                                </motion.div>
                            ) : isSuccess ? (
                                <motion.div 
                                    key="success"
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="flex items-center justify-center gap-2"
                                >
                                    <CheckCircle2 className="w-4 h-4" />
                                    <span>İndirildi</span>
                                </motion.div>
                            ) : (
                                <motion.div 
                                    key="idle"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="flex items-center justify-center gap-2"
                                >
                                    <Download className="w-4 h-4" />
                                    <span>{format === 'pdf' ? 'PDF İndir' : 'Excel İndir'}</span>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </Button>
                </div>
            </motion.div>
        </div>
    );
}
