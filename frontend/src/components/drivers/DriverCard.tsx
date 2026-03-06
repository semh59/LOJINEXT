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
                        <div className="w-16 h-16 rounded-[24px] bg-gradient-to-br from-[#d006f9]/20 to-[#d006f9]/5 flex items-center justify-center border border-[#d006f9]/20 group-hover:scale-105 transition-transform duration-500 shadow-[0_0_30px_rgba(208,6,249,0.1)]">
                            <User className="w-8 h-8 text-[#d006f9]" />
                        </div>
                        {driver.aktif && (
                            <div title="Aktif" className="absolute -bottom-1 -right-1 w-5 h-5 bg-emerald-500 border-2 border-[#050b0e] rounded-full flex items-center justify-center shadow-[0_0_10px_rgba(16,185,129,0.5)]">
                                <ShieldCheck className="w-3 h-3 text-white" />
                            </div>
                        )}
                    </div>
                    <div>
                        <h3 className="text-xl font-black text-white leading-tight tracking-tight uppercase">{driver.ad_soyad}</h3>
                        <div className="flex items-center gap-2 mt-1">
                            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-white/5 px-2 py-0.5 rounded-lg border border-white/5">
                                {driver.ehliyet_sinifi} Sınıfı
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                        onClick={() => onEdit(driver)}
                        className="p-2.5 rounded-xl hover:bg-white/10 text-slate-400 hover:text-[#d006f9] transition-all"
                    >
                        <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => driver.id && onDelete(driver.id)}
                        className="p-2.5 rounded-xl hover:bg-red-500/10 text-slate-400 hover:text-red-500 transition-all"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Performance Metric */}
            <div className="bg-black/20 rounded-2xl p-4 border border-white/5 mb-6 flex items-center justify-between shadow-inner">
                <div>
                    <div className="flex items-center gap-2 text-slate-500 mb-0.5">
                        <Award className="w-3.5 h-3.5" />
                        <span className="text-[10px] font-bold uppercase tracking-widest">Sürücü Puanı</span>
                    </div>
                    <div className="flex items-baseline gap-1">
                        <span className={cn(
                            "text-3xl font-black leading-none",
                            isGoodScore ? "text-[#d006f9] drop-shadow-[0_0_10px_rgba(208,6,249,0.3)]" : "text-amber-500"
                        )}>
                            {score.toFixed(2)}
                        </span>
                        <span className="text-[10px] font-bold text-slate-600 uppercase tracking-tighter">/ 2.00</span>
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
                                        ? "fill-amber-400 text-amber-400" 
                                        : "text-neutral-200"
                                )}
                            />
                        ))}
                    </div>
                    <span className="text-[9px] font-black text-slate-600 uppercase tracking-widest">E-Skor</span>
                </div>
            </div>

            {/* Contact Info */}
            <div className="space-y-3 mb-8">
                <div className="flex items-center gap-3 text-slate-400 transition-colors hover:text-[#d006f9] cursor-pointer group/item">
                    <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/5 flex items-center justify-center group-hover/item:border-[#d006f9]/30">
                        <Phone className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-bold text-slate-200">{driver.telefon || 'Belirtilmedi'}</span>
                </div>
                <div className="flex items-center gap-3 text-slate-400">
                    <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/5 flex items-center justify-center">
                        <Calendar className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-bold text-slate-200">
                        {driver.ise_baslama ? new Date(driver.ise_baslama).toLocaleDateString('tr-TR') : '---'}
                    </span>
                </div>
            </div>

            {/* Actions */}
            <div className="mt-auto pt-6 border-t border-white/5 flex items-center gap-3">
                <button
                    onClick={() => onScoreClick(driver)}
                    className="flex-1 h-11 rounded-xl bg-[#d006f9]/10 hover:bg-[#d006f9] text-[#d006f9] hover:text-white text-xs font-bold uppercase tracking-widest transition-all duration-300 flex items-center justify-center gap-2 active:scale-95 border border-[#d006f9]/20"
                >
                    <Star className="w-4 h-4" /> Puanla
                </button>
            </div>
        </motion.div>
    )
}
