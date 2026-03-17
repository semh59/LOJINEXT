import { useRef } from 'react'
import { FuelRecord } from '../../types'
import { motion, AnimatePresence } from 'framer-motion'
import { Edit2, Trash2, Fuel } from 'lucide-react'
import { useVirtualizer } from '@tanstack/react-virtual'

interface FuelTableProps {
    records: FuelRecord[]
    loading: boolean
    onEdit: (record: FuelRecord) => void
    onDelete: (record: FuelRecord) => void
}

export function FuelTable({ records, loading, onEdit, onDelete }: FuelTableProps) {
    const parentRef = useRef<HTMLDivElement>(null);

    const virtualizer = useVirtualizer({
        count: records.length,
        getScrollElement: () => parentRef.current,
        estimateSize: () => 80,
        overscan: 10,
    });

    if (loading) {
        return (
            <div className="space-y-4 p-8">
                {[...Array(5)].map((_, i) => (
                    <div key={i} className="h-16 w-full animate-pulse bg-surface border border-border rounded-xl" />
                ))}
            </div>
        );
    }

    if (!records.length) {
        return (
            <div className="flex flex-col items-center justify-center p-20 text-center bg-surface border border-border rounded-xl">
                <div className="w-20 h-20 bg-bg-elevated rounded-full flex items-center justify-center mb-4">
                    <span className="material-symbols-outlined text-4xl text-secondary font-variation-fill">local_gas_station</span>
                </div>
                <h3 className="text-xl font-black text-primary tracking-tight">Kayıt Bulunamadı</h3>
                <p className="text-secondary font-medium mt-1">Belirlediğiniz filtrelere uygun yakıt kaydı bulunmuyor.</p>
            </div>
        );
    }

    const gridTemplate = "minmax(120px, 1fr) minmax(130px, 1fr) minmax(200px, 1.5fr) minmax(130px, 1fr) minmax(130px, 1fr) minmax(140px, 1fr) 100px"

    return (
        <div 
            ref={parentRef}
            className="w-full overflow-auto max-h-[700px] bg-surface border border-border rounded-2xl custom-scrollbar"
        >
            <div className="min-w-[1050px]">
                {/* Header */}
                <div 
                    className="sticky top-0 z-20 backdrop-blur-md bg-bg-elevated/90 border-b border-border grid items-center px-6 py-4"
                    style={{ gridTemplateColumns: gridTemplate }}
                >
                    <div className="text-[10px] font-bold text-secondary uppercase tracking-widest">Tarih & Saat</div>
                    <div className="text-[10px] font-bold text-secondary uppercase tracking-widest">Araç Plakası</div>
                    <div className="text-[10px] font-bold text-secondary uppercase tracking-widest">İstasyon / Fiş No</div>
                    <div className="text-[10px] font-bold text-secondary uppercase tracking-widest text-right">Miktar (Litre)</div>
                    <div className="text-[10px] font-bold text-secondary uppercase tracking-widest text-right">Litre Fiyatı</div>
                    <div className="text-[10px] font-bold text-secondary uppercase tracking-widest text-right">Toplam Tutar</div>
                    <div className="text-[10px] font-bold text-secondary uppercase tracking-widest text-center">İşlem</div>
                </div>

                {/* Virtual Body */}
                <div
                    style={{
                        height: `${virtualizer.getTotalSize()}px`,
                        width: '100%',
                        position: 'relative',
                    }}
                >
                    <AnimatePresence mode="popLayout">
                        {virtualizer.getVirtualItems().map((virtualRow) => {
                            const record = records[virtualRow.index];
                            if (!record) return null;

                            return (
                                <motion.div
                                    key={record.id}
                                    layout
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="group hover:bg-bg-elevated hover:shadow-sm transition-all border-b border-border absolute w-full left-0 grid items-center px-6 py-2"
                                    style={{
                                        height: `${virtualRow.size}px`,
                                        top: `${virtualRow.start}px`,
                                        gridTemplateColumns: gridTemplate
                                    }}
                                >
                                    <div className="flex flex-col">
                                        <span className="text-primary text-sm font-bold">
                                            {new Date(record.tarih).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' })}
                                        </span>
                                        <span className="text-secondary text-[10px] font-bold uppercase">{(record as any).saat || '12:00'}</span>
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <div className="size-2 rounded-full bg-success shadow-sm shadow-success/20 animate-pulse"></div>
                                        <span className="text-primary text-sm font-black uppercase tracking-tight">{record.plaka}</span>
                                    </div>

                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 shrink-0 rounded-lg bg-bg-elevated border border-border flex items-center justify-center">
                                            <Fuel className="w-4 h-4 text-secondary" />
                                        </div>
                                        <div className="flex flex-col min-w-0 pr-4">
                                            <span className="text-primary text-sm font-bold truncate">{record.istasyon || 'Bilinmiyor'}</span>
                                            <span className="text-secondary text-[10px] font-bold truncate">Fiş: {record.fis_no || '-'}</span>
                                        </div>
                                    </div>

                                    <div className="text-right">
                                        <span className="text-primary font-mono text-sm tabular-nums">{record.litre.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} L</span>
                                    </div>

                                    <div className="text-right">
                                        <span className="bg-success/10 text-success px-2 py-1 rounded text-xs font-bold whitespace-nowrap tabular-nums">
                                            {(record.fiyat_tl || 0).toLocaleString('tr-TR', { style: 'currency', currency: 'TRY' })} /L
                                        </span>
                                    </div>

                                    <div className="text-right">
                                        <span className="text-primary font-bold text-sm tabular-nums">
                                            {record.toplam_tutar.toLocaleString('tr-TR', { style: 'currency', currency: 'TRY' })}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button 
                                            onClick={() => onEdit(record)}
                                            className="p-2 rounded-lg text-secondary hover:text-accent hover:bg-accent/10 transition-all"
                                        >
                                            <Edit2 className="w-4 h-4" />
                                        </button>
                                        <button 
                                            onClick={() => onDelete(record)}
                                            className="p-2 rounded-lg text-secondary hover:text-danger hover:bg-danger/10 transition-all"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </motion.div>
                            )
                        })}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    )
}
