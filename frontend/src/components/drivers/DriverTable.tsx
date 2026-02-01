import { motion } from 'framer-motion'
import { Driver } from '../../types'
import { Edit2, Trash2, Star, User, Phone, Calendar, ShieldCheck } from 'lucide-react'
import { cn } from '../../lib/utils'
import EmptyState from '../common/EmptyState'

interface DriverTableProps {
    drivers: Driver[]
    onEdit: (driver: Driver) => void
    onDelete: (driver: Driver) => void
    onScoreClick: (driver: Driver) => void
    loading?: boolean
}

export function DriverTable({ drivers, onEdit, onDelete, onScoreClick, loading }: DriverTableProps) {
    if (loading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 animate-pulse">
                {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-72 glass rounded-[32px] bg-white/40 border border-white/20" />
                ))}
            </div>
        )
    }

    if (drivers.length === 0) {
        return (
            <EmptyState
                icon={User}
                title="Sürücü Bulunamadı"
                description="Kayıtlı sürücü listesi boş veya filtre eşleşmiyor."
            />
        )
    }

    const renderPerformance = (score: number, manual?: number) => {
        const starCount = Math.round((score / 2.0) * 5)
        return (
            <div className="flex flex-col gap-1 group/score relative">
                <div className="flex items-center gap-0.5">
                    {[1, 2, 3, 4, 5].map((i) => (
                        <Star
                            key={i}
                            className={cn(
                                "w-3 h-3 transition-colors",
                                i <= starCount ? "fill-amber-400 text-amber-400" : "text-neutral-200"
                            )}
                        />
                    ))}
                </div>
                <div className="flex flex-col gap-1 relative">
                    <span className="text-[10px] font-black text-brand-dark/80 tracking-tighter uppercase whitespace-nowrap flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                        Hibrit: {score.toFixed(2)}
                    </span>
                    {manual !== undefined && (
                        <div className="flex items-center gap-1.5">
                            <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                            <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-tighter">Manuel: {manual.toFixed(1)}</span>
                        </div>
                    )}
                </div>
            </div>
        )
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {drivers.map((driver, index) => {
                if (!driver?.id) return null;

                return (
                    <motion.div
                        key={driver.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="group relative glass rounded-[32px] p-6 hover:shadow-floating transition-all duration-500 hover:-translate-y-2 border border-white/40 overflow-hidden"
                    >
                        {/* Status Badge */}
                        <div className="absolute top-4 right-4 group-hover:scale-110 transition-transform">
                            <span className={cn(
                                "flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border shadow-sm",
                                driver.aktif
                                    ? "bg-success/10 text-success-dark border-success/20"
                                    : "bg-danger/10 text-danger-dark border-danger/20"
                            )}>
                                <span className={cn(
                                    "w-1.5 h-1.5 rounded-full",
                                    driver.aktif ? "bg-success animate-pulse shadow-[0_0_5px_rgba(34,197,94,0.5)]" : "bg-danger"
                                )} />
                                {driver.aktif ? 'AKTİF' : 'PASİF'}
                            </span>
                        </div>

                        {/* Avatar & Basic Info */}
                        <div className="flex flex-col items-center text-center mb-6">
                            <div className="relative mb-4 group-hover:rotate-3 transition-transform duration-500">
                                <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary/20 to-brand/20 flex items-center justify-center text-primary text-3xl font-black border-2 border-white shadow-xl relative z-10">
                                    {driver.ad_soyad[0]?.toUpperCase()}
                                </div>
                                <div className="absolute -inset-2 bg-gradient-to-tr from-primary/10 to-transparent blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>
                            <h4 className="text-xl font-black text-brand-dark tracking-tighter mb-1 truncate w-full">
                                {driver.ad_soyad}
                            </h4>
                            <div className="flex items-center gap-2 text-primary/80 font-bold text-xs uppercase tracking-widest bg-primary/5 px-2 py-0.5 rounded-lg border border-primary/10">
                                <ShieldCheck className="w-3 h-3" />
                                {driver.ehliyet_sinifi || 'B'} Sınıfı
                            </div>
                        </div>

                        {/* Contact & Meta Grid */}
                        <div className="space-y-3 mb-8">
                            <div className="flex items-center justify-between p-3 rounded-2xl bg-white/50 border border-white shadow-inner">
                                <div className="flex items-center gap-3">
                                    <div className="p-1.5 bg-neutral-100 rounded-lg">
                                        <Phone className="w-3.5 h-3.5 text-neutral-400" />
                                    </div>
                                    <span className="text-xs font-bold text-neutral-600 truncate max-w-[120px]">
                                        {driver.telefon_masked || driver.telefon || '-'}
                                    </span>
                                </div>
                                {renderPerformance(driver.score || 1.0, driver.manual_score)}
                            </div>

                            <div className="flex items-center gap-3 px-3">
                                <Calendar className="w-3.5 h-3.5 text-neutral-400" />
                                <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">
                                    Giriş: {driver.ise_baslama ? new Date(driver.ise_baslama).toLocaleDateString('tr-TR') : '-'}
                                </span>
                            </div>
                        </div>

                        {/* Actions Overlay */}
                        <div className="flex items-center gap-2 pt-4 border-t border-neutral-100/50">
                            <button
                                onClick={() => onScoreClick(driver)}
                                className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 text-white text-[10px] font-black uppercase tracking-widest hover:shadow-lg hover:shadow-orange-200 transition-all duration-300 active:scale-95"
                            >
                                <Star className="w-3.5 h-3.5 fill-white" /> Puanla
                            </button>
                            <button
                                onClick={() => onEdit(driver)}
                                className="p-2.5 rounded-xl bg-white border border-neutral-100 text-neutral-400 hover:text-primary hover:border-primary/30 transition-all duration-300"
                            >
                                <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                                onClick={() => onDelete(driver)}
                                className="p-2.5 rounded-xl bg-danger/5 text-danger hover:bg-danger hover:text-white transition-all duration-300"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>

                        {/* Abstract Decorative Line */}
                        <div className="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-transparent via-primary/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    </motion.div>
                );
            })}
        </div>
    )
}
