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
        <div className="bg-[#1a0121]/60 backdrop-blur-md rounded-[24px] border border-[#d006f9]/20 shadow-[0_0_15px_rgba(208,6,249,0.05)] overflow-hidden">
            <div className="overflow-x-auto custom-scrollbar">
                <div className="min-w-[800px]">
                    {/* Header */}
                    <div 
                        className="bg-black/40 grid items-center px-6 py-4 border-b border-[#d006f9]/20"
                        style={{ gridTemplateColumns: gridTemplate }}
                    >
                        <div className="text-[11px] font-black text-white/40 uppercase tracking-widest">Sürücü</div>
                        <div className="text-[11px] font-black text-white/40 uppercase tracking-widest">İletişim</div>
                        <div className="text-[11px] font-black text-white/40 uppercase tracking-widest">Puan</div>
                        <div className="text-[11px] font-black text-white/40 uppercase tracking-widest">Durum</div>
                        <div className="text-[11px] font-black text-white/40 uppercase tracking-widest text-right">İşlemler</div>
                    </div>

                    <div className="divide-y divide-[#d006f9]/10">
                        <AnimatePresence mode="popLayout">
                            {drivers.map((driver, idx) => (
                                <motion.div
                                    key={driver.id}
                                    layout
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, scale: 0.98 }}
                                    transition={{ duration: 0.2, delay: idx * 0.02 }}
                                    className="group hover:bg-[#1a0121]/80 transition-all grid items-center px-6 py-5"
                                    style={{ gridTemplateColumns: gridTemplate }}
                                >
                                    <div className="flex items-center gap-3 min-w-0">
                                        <div className="w-10 h-10 rounded-xl bg-[#d006f9]/10 border border-[#d006f9]/30 shadow-[0_0_10px_rgba(208,6,249,0.2)] flex items-center justify-center text-[#d006f9] font-black shrink-0">
                                            {driver.ad_soyad[0]}
                                        </div>
                                        <div className="flex flex-col min-w-0">
                                            <span className="text-sm font-black text-white truncate">{driver.ad_soyad}</span>
                                            <span className="text-[10px] font-bold text-white/50 uppercase truncate">{driver.ehliyet_sinifi} Sınıfı</span>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 text-xs font-bold text-white/70 tabular-nums">
                                        <Phone className="w-3.5 h-3.5 text-[#d006f9]/60" />
                                        {driver.telefon || '-'}
                                    </div>

                                    <div className="flex items-center gap-0.5">
                                        {[...Array(5)].map((_, i) => (
                                            <Star 
                                                key={i} 
                                                className={cn("w-3.5 h-3.5", i < (driver.score || 0) ? "text-amber-400 fill-amber-400 drop-shadow-[0_0_5px_rgba(251,191,36,0.5)]" : "text-white/10")} 
                                            />
                                        ))}
                                    </div>

                                    <div>
                                        <div className={cn(
                                            "inline-flex items-center gap-2 px-3 py-1 rounded-xl text-[10px] font-black uppercase tracking-widest border",
                                            driver.aktif ? "bg-[#0df259]/10 text-[#0df259] border-[#0df259]/30" : "bg-white/5 text-white/60 border-white/10"
                                        )}>
                                            <span className={cn(
                                                "w-1.5 h-1.5 rounded-full",
                                                driver.aktif ? "bg-[#0df259] shadow-[0_0_5px_#0df259] animate-pulse" : "bg-white/40"
                                            )}></span>
                                            {driver.aktif ? 'Aktif' : 'Pasif'}
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-end gap-1">
                                        <button onClick={() => onPerformanceClick(driver)} className="p-2.5 rounded-xl hover:bg-indigo-500/10 text-white/40 hover:text-indigo-400 transition-all focus:outline-none" title="AI Analiz"><BrainCircuit className="w-4.5 h-4.5" /></button>
                                        <button onClick={() => onScoreClick(driver)} className="p-2.5 rounded-xl hover:bg-amber-500/10 text-white/40 hover:text-amber-400 transition-all focus:outline-none" title="Puanla"><Award className="w-4.5 h-4.5" /></button>
                                        <button onClick={() => onEdit(driver)} className="p-2.5 rounded-xl hover:bg-[#d006f9]/10 text-white/40 hover:text-[#d006f9] transition-all focus:outline-none"><Edit2 className="w-4.5 h-4.5" /></button>
                                        <button onClick={() => onDelete(driver)} className="p-2.5 rounded-xl hover:bg-red-500/10 text-white/40 hover:text-red-400 transition-all focus:outline-none"><Trash2 className="w-4.5 h-4.5" /></button>
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
