import { motion, AnimatePresence } from 'framer-motion'
import { Star, Phone, Award, Edit2, Trash2, BrainCircuit } from 'lucide-react'
import { Driver } from '../../types'
import { cn } from '../../lib/utils'

interface DriverTableProps {
    drivers: Driver[]
    onEdit: (driver: Driver) => void
    onDelete: (driver: Driver) => void
    onScoreClick: (driver: Driver) => void
    onPerformanceClick: (driver: Driver) => void
}

export function DriverTable({ drivers, onEdit, onDelete, onScoreClick, onPerformanceClick }: DriverTableProps) {
    const gridTemplate = "1fr 140px 140px 140px 160px";

    return (
        <div className="bg-surface rounded-none border-none overflow-hidden">
            <div className="overflow-x-auto custom-scrollbar">
                <div className="min-w-[800px]">
                    {/* Header */}
                    <div 
                        className="bg-bg-elevated/50 grid items-center px-6 py-4 border-b border-border"
                        style={{ gridTemplateColumns: gridTemplate }}
                    >
                        <div className="text-[11px] font-bold text-secondary uppercase tracking-widest">Sürücü</div>
                        <div className="text-[11px] font-bold text-secondary uppercase tracking-widest">İletişim</div>
                        <div className="text-[11px] font-bold text-secondary uppercase tracking-widest">Puan</div>
                        <div className="text-[11px] font-bold text-secondary uppercase tracking-widest">Durum</div>
                        <div className="text-[11px] font-bold text-secondary uppercase tracking-widest text-right">İşlemler</div>
                    </div>

                    <div className="divide-y divide-border">
                        <AnimatePresence mode="popLayout">
                            {drivers.map((driver, idx) => (
                                <motion.div
                                    key={driver.id}
                                    layout
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, scale: 0.98 }}
                                    transition={{ duration: 0.2, delay: idx * 0.02 }}
                                    className="group hover:bg-bg-elevated/30 transition-all grid items-center px-6 py-4"
                                    style={{ gridTemplateColumns: gridTemplate }}
                                >
                                    <div className="flex items-center gap-3 min-w-0">
                                        <div className="w-10 h-10 rounded-lg bg-bg-elevated border border-border flex items-center justify-center text-accent font-bold shrink-0 shadow-sm">
                                            {driver.ad_soyad[0]}
                                        </div>
                                        <div className="flex flex-col min-w-0">
                                            <span className="text-sm font-bold text-primary truncate">{driver.ad_soyad}</span>
                                            <span className="text-[10px] font-bold text-secondary uppercase truncate">{driver.ehliyet_sinifi} Sınıfı</span>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 text-xs font-medium text-primary tabular-nums">
                                        <Phone className="w-3.5 h-3.5 text-secondary" />
                                        {driver.telefon || '-'}
                                    </div>

                                    <div className="flex items-center gap-0.5">
                                        {[...Array(5)].map((_, i) => (
                                            <Star 
                                                key={i} 
                                                className={cn("w-3.5 h-3.5", i < (driver.score || 0) ? "text-warning fill-warning" : "text-border")} 
                                            />
                                        ))}
                                    </div>

                                    <div>
                                        <div className={cn(
                                            "inline-flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-tight border",
                                            driver.aktif ? "bg-success/10 text-success border-success/20" : "bg-bg-elevated text-secondary border-border"
                                        )}>
                                            <span className={cn(
                                                "w-1.5 h-1.5 rounded-full",
                                                driver.aktif ? "bg-success shadow-[0_0_8px_rgba(34,197,94,0.3)]" : "bg-border"
                                            )}></span>
                                            {driver.aktif ? 'Aktif' : 'Pasif'}
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-end gap-1">
                                        <button onClick={() => onPerformanceClick(driver)} className="p-2 rounded-lg hover:bg-info/10 text-secondary hover:text-info transition-all focus:outline-none" title="AI Analiz"><BrainCircuit className="w-4 h-4" /></button>
                                        <button onClick={() => onScoreClick(driver)} className="p-2 rounded-lg hover:bg-warning/10 text-secondary hover:text-warning transition-all focus:outline-none" title="Puanla"><Award className="w-4 h-4" /></button>
                                        <button onClick={() => onEdit(driver)} className="p-2 rounded-lg hover:bg-accent/10 text-secondary hover:text-accent transition-all focus:outline-none"><Edit2 className="w-4 h-4" /></button>
                                        <button onClick={() => onDelete(driver)} className="p-2 rounded-lg hover:bg-danger/10 text-secondary hover:text-danger transition-all focus:outline-none"><Trash2 className="w-4 h-4" /></button>
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                </div>
            </div>
        </div>
    )
}
