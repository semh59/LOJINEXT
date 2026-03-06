import { motion } from 'framer-motion'
import { Star, Edit2, Trash2, BrainCircuit } from 'lucide-react'
import { Driver } from '../../types'
import { cn } from '../../lib/utils'

interface DriverGridProps {
    drivers: Driver[]
    onEdit: (driver: Driver) => void
    onDelete: (driver: Driver) => void
    onPerformanceClick: (driver: Driver) => void
}

export function DriverGrid({ drivers, onEdit, onDelete, onPerformanceClick }: DriverGridProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {drivers.map((driver, idx) => (
                <motion.div
                    key={driver.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="bg-[#1a0121]/60 backdrop-blur-md p-6 rounded-[24px] border border-[#d006f9]/20 shadow-[0_0_15px_rgba(208,6,249,0.05)] transition-all hover:bg-[#1a0121]/80 hover:border-[#d006f9]/40 group flex flex-col"
                >
                    <div className="flex items-start justify-between mb-6">
                        <div className="w-12 h-12 rounded-2xl bg-[#d006f9]/10 flex items-center justify-center text-[#d006f9] font-black text-xl border border-[#d006f9]/20 shadow-[0_0_10px_rgba(208,6,249,0.2)]">
                            {driver.ad_soyad[0]}
                        </div>
                        <div className={cn(
                            "px-2 py-0.5 rounded-lg text-[9px] font-black uppercase tracking-tighter border flex items-center gap-1.5",
                            driver.aktif ? "bg-[#0df259]/10 text-[#0df259] border-[#0df259]/30" : "bg-white/5 text-white/60 border-white/10"
                        )}>
                            <span className={cn(
                                "w-1.5 h-1.5 rounded-full",
                                driver.aktif ? "bg-[#0df259] shadow-[0_0_5px_#0df259] animate-pulse" : "bg-white/40"
                            )}></span>
                            {driver.aktif ? 'Aktif' : 'Pasif'}
                        </div>
                    </div>
                    <h4 className="text-base font-black text-white mb-1">{driver.ad_soyad}</h4>
                    <p className="text-xs font-bold text-white/50 mb-4">{driver.ehliyet_sinifi} Sınıfı Ehliyet</p>
                    <div className="flex items-center justify-between mt-auto pt-4 border-t border-[#d006f9]/10">
                        <div className="flex items-center gap-0.5">
                            {[...Array(5)].map((_, i) => (
                                <Star 
                                    key={i} 
                                    className={cn("w-3.5 h-3.5", i < (driver.score || 0) ? "text-amber-400 fill-amber-400 drop-shadow-[0_0_5px_rgba(251,191,36,0.5)]" : "text-white/10")} 
                                />
                            ))}
                        </div>
                        <div className="flex gap-1">
                            <button onClick={() => onPerformanceClick(driver)} className="p-2 rounded-lg hover:bg-indigo-500/10 text-white/40 hover:text-indigo-400 focus:outline-none transition-colors" title="AI Analiz"><BrainCircuit className="w-4 h-4" /></button>
                            <button onClick={() => onEdit(driver)} className="p-2 rounded-lg hover:bg-[#d006f9]/10 text-white/40 hover:text-[#d006f9] focus:outline-none transition-colors" title="Düzenle"><Edit2 className="w-4 h-4" /></button>
                            <button onClick={() => onDelete(driver)} className="p-2 rounded-lg hover:bg-red-500/10 text-white/40 hover:text-red-400 focus:outline-none transition-colors" title="Sil"><Trash2 className="w-4 h-4" /></button>
                        </div>
                    </div>
                </motion.div>
            ))}
        </div>
    )
}

