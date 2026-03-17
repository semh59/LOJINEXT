import { Driver } from '../../types'
import { motion } from 'framer-motion'
import { User, Phone, Star, Edit2, Trash2, Calendar, ShieldCheck, Award } from 'lucide-react'
import { cn } from '../../lib/utils'

interface DriverCardProps {
    driver: Driver
    onEdit: (driver: Driver) => void
    onDelete: (id: number) => void
    onScoreClick: (driver: Driver) => void
}

export function DriverCard({ driver, onEdit, onDelete, onScoreClick }: DriverCardProps) {
    const score = driver.score || 0
    const isGoodScore = score >= 1.5

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card-premium h-full flex flex-col p-6 group"
        >
            {/* Header / Avatar */}
            <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                    <div className="relative">
                        <div className="w-16 h-16 rounded-[24px] bg-accent/5 flex items-center justify-center border border-accent/20 group-hover:scale-105 transition-transform duration-500 shadow-lg shadow-accent/5">
                            <User className="w-8 h-8 text-accent" />
                        </div>
                        {driver.aktif && (
                            <div title="Aktif" className="absolute -bottom-1 -right-1 w-5 h-5 bg-success border-2 border-bg-base rounded-full flex items-center justify-center shadow-lg shadow-success/20">
                                <ShieldCheck className="w-3 h-3 text-bg-base" />
                            </div>
                        )}
                    </div>
                    <div>
                        <h3 className="text-xl font-black text-primary leading-tight tracking-tight uppercase">{driver.ad_soyad}</h3>
                        <div className="flex items-center gap-2 mt-1">
                            <span className="text-[10px] font-bold text-secondary uppercase tracking-widest bg-bg-elevated px-2 py-0.5 rounded-lg border border-border">
                                {driver.ehliyet_sinifi} Sınıfı
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                        onClick={() => onEdit(driver)}
                        className="p-2.5 rounded-xl hover:bg-bg-elevated text-secondary hover:text-accent transition-all"
                    >
                        <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => driver.id && onDelete(driver.id)}
                        className="p-2.5 rounded-xl hover:bg-danger/10 text-secondary hover:text-danger transition-all"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Performance Metric */}
            <div className="bg-bg-elevated/40 rounded-2xl p-4 border border-border mb-6 flex items-center justify-between shadow-inner">
                <div>
                    <div className="flex items-center gap-2 text-secondary mb-0.5">
                        <Award className="w-3.5 h-3.5" />
                        <span className="text-[10px] font-bold uppercase tracking-widest">Sürücü Puanı</span>
                    </div>
                    <div className="flex items-baseline gap-1">
                        <span className={cn(
                            "text-3xl font-black leading-none",
                            isGoodScore ? "text-accent drop-shadow-[0_0_10px_var(--accent-glow)]" : "text-warning"
                        )}>
                            {score.toFixed(2)}
                        </span>
                        <span className="text-[10px] font-bold text-secondary uppercase tracking-tighter">/ 2.00</span>
                    </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                    <div className="flex gap-0.5">
                        {[...Array(5)].map((_, i) => (
                            <Star 
                                key={i} 
                                className={cn(
                                    "w-3.5 h-3.5",
                                    i < Math.round(score * 2.5) 
                                        ? "fill-warning text-warning" 
                                        : "text-border"
                                )}
                            />
                        ))}
                    </div>
                    <span className="text-[9px] font-black text-secondary uppercase tracking-widest">E-Skor</span>
                </div>
            </div>

            {/* Contact Info */}
            <div className="space-y-3 mb-8">
                <div className="flex items-center gap-3 text-secondary transition-colors hover:text-accent cursor-pointer group/item">
                    <div className="w-8 h-8 rounded-lg bg-bg-elevated border border-border flex items-center justify-center group-hover/item:border-accent/30">
                        <Phone className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-bold text-primary">{driver.telefon || 'Belirtilmedi'}</span>
                </div>
                <div className="flex items-center gap-3 text-secondary">
                    <div className="w-8 h-8 rounded-lg bg-bg-elevated border border-border flex items-center justify-center">
                        <Calendar className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-bold text-primary">
                        {driver.ise_baslama ? new Date(driver.ise_baslama).toLocaleDateString('tr-TR') : '---'}
                    </span>
                </div>
            </div>

            {/* Actions */}
            <div className="mt-auto pt-6 border-t border-border flex items-center gap-3">
                <button
                    onClick={() => onScoreClick(driver)}
                    className="flex-1 h-11 rounded-xl bg-accent/10 hover:bg-accent text-accent hover:text-bg-base text-xs font-bold uppercase tracking-widest transition-all duration-300 flex items-center justify-center gap-2 active:scale-95 border border-accent/20"
                >
                    <Star className="w-4 h-4" /> Puanla
                </button>
            </div>
        </motion.div>
    )
}
