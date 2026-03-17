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
                    className="bg-surface p-6 rounded-[12px] border border-border shadow-sm transition-all hover:shadow-md hover:border-accent group flex flex-col"
                >
                    <div className="flex items-start justify-between mb-6">
                        <div className="w-12 h-12 rounded-[10px] bg-bg-elevated flex items-center justify-center text-accent font-bold text-xl border border-border shadow-sm">
                            {driver.ad_soyad[0]}
                        </div>
                        <div className={cn(
                            "px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-tight border flex items-center gap-1.5",
                            driver.aktif ? "bg-success/10 text-success border-success/20" : "bg-bg-elevated text-secondary border-border"
                        )}>
                            <span className={cn(
                                "w-1.5 h-1.5 rounded-full",
                                driver.aktif ? "bg-success shadow-[0_0_8px_rgba(34,197,94,0.3)]" : "bg-border"
                            )}></span>
                            {driver.aktif ? 'Aktif' : 'Pasif'}
                        </div>
                    </div>
                    <h4 className="text-base font-bold text-primary mb-1">{driver.ad_soyad}</h4>
                    <p className="text-xs font-medium text-secondary mb-4">{driver.ehliyet_sinifi} Sınıfı Ehliyet</p>
                    <div className="flex items-center justify-between mt-auto pt-4 border-t border-border">
                        <div className="flex items-center gap-0.5">
                            {[...Array(5)].map((_, i) => (
                                <Star 
                                    key={i} 
                                    className={cn("w-3.5 h-3.5", i < (driver.score || 0) ? "text-warning fill-warning" : "text-border")} 
                                />
                            ))}
                        </div>
                        <div className="flex gap-1">
                            <button onClick={() => onPerformanceClick(driver)} className="p-2 rounded-lg hover:bg-info/10 text-secondary hover:text-info focus:outline-none transition-colors" title="AI Analiz"><BrainCircuit className="w-4 h-4" /></button>
                            <button onClick={() => onEdit(driver)} className="p-2 rounded-lg hover:bg-accent/10 text-secondary hover:text-accent focus:outline-none transition-colors" title="Düzenle"><Edit2 className="w-4 h-4" /></button>
                            <button onClick={() => onDelete(driver)} className="p-2 rounded-lg hover:bg-danger/10 text-secondary hover:text-danger focus:outline-none transition-colors" title="Sil"><Trash2 className="w-4 h-4" /></button>
                        </div>
                    </div>
                </motion.div>
            ))}
        </div>
    )
}

