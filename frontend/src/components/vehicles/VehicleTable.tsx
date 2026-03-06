import { useState, useEffect } from 'react'
import { Vehicle } from '../../types'
import { Edit2, Trash2, Truck, Gauge, Calendar, Droplet, Activity } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '../../lib/utils'
import { SkeletonTable } from './SkeletonTable'

interface VehicleTableProps {
    vehicles: Vehicle[]
    loading: boolean
    onEdit: (vehicle: Vehicle) => void
    onDelete: (vehicle: Vehicle) => void | Promise<void>
    onViewDetail: (vehicle: Vehicle) => void
}

export function VehicleTable({ vehicles, loading, onEdit, onDelete, onViewDetail }: VehicleTableProps) {
    const [deletingIds, setDeletingIds] = useState<Set<number>>(new Set())
    const [deletedIds, setDeletedIds] = useState<Set<number>>(new Set())

    useEffect(() => {
        setDeletedIds(new Set())
        setDeletingIds(new Set())
    }, [vehicles])

    const handleOptimisticDelete = async (vehicle: Vehicle) => {
        if (!vehicle.id) return
        
        const id = vehicle.id
        setDeletedIds(prev => new Set([...prev, id]))
        setDeletingIds(prev => new Set([...prev, id]))

        try {
            await onDelete(vehicle)
        } catch (error) {
            setDeletedIds(prev => {
                const next = new Set(prev)
                next.delete(id)
                return next
            })
        } finally {
            setDeletingIds(prev => {
                const next = new Set(prev)
                next.delete(id)
                return next
            })
        }
    }

    if (loading) {
        return <SkeletonTable rows={5} />
    }

    if (vehicles.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-16 text-center border-2 border-dashed border-[#d006f9]/20 rounded-[32px] bg-[#1a0121]/40 backdrop-blur-md shadow-[inset_0_2px_20px_rgba(0,0,0,0.2)]">
                <div className="w-20 h-20 bg-[#d006f9]/10 rounded-2xl flex items-center justify-center mb-6 border border-[#d006f9]/30 shadow-[0_0_30px_rgba(208,6,249,0.2)]">
                    <Truck className="w-10 h-10 text-[#d006f9]" />
                </div>
                <h3 className="text-2xl font-black text-white mb-2">Henüz Araç Eklenmemiş</h3>
                <p className="text-white/50 max-w-sm text-sm">
                    Filo yönetimine başlamak için sağ üstteki butondan yeni bir araç ekleyerek operasyonlarınızı başlatın.
                </p>
            </div>
        )
    }

    return (
        <div className="w-full space-y-6">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-black text-white flex items-center gap-3">
                    <div className="w-10 h-10 bg-[#d006f9]/20 border border-[#d006f9]/40 rounded-xl flex items-center justify-center text-[#d006f9] shadow-[0_0_15px_rgba(208,6,249,0.3)]">
                        <Truck className="w-5 h-5" />
                    </div>
                    Filo Araçları
                </h2>
                <div className="text-sm font-bold text-white/50 bg-black/40 px-4 py-2 rounded-xl border border-white/5 shadow-[inset_0_2px_4px_rgba(0,0,0,0.3)]">
                    Toplam: <span className="text-[#d006f9] ml-1">{vehicles.filter(v => !deletedIds.has(v.id!)).length} Araç</span>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                <AnimatePresence>
                    {vehicles
                        .filter(v => v.id && !deletedIds.has(v.id))
                        .map((vehicle, index) => (
                            <motion.div
                                key={vehicle.id}
                                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.9, y: -20 }}
                                transition={{ duration: 0.3, delay: index * 0.05 }}
                                className={cn(
                                    "bg-[#1a0121]/80 backdrop-blur-xl border border-[#d006f9]/30 rounded-[24px] p-6 shadow-[0_0_30px_rgba(208,6,249,0.1)] transition-all hover:-translate-y-1 hover:shadow-[0_0_40px_rgba(208,6,249,0.2)] hover:border-[#d006f9]/50 flex flex-col relative overflow-hidden group",
                                    vehicle.id && deletingIds.has(vehicle.id) && "opacity-50 grayscale pointer-events-none"
                                )}
                            >
                                {/* Background glow effect on hover */}
                                <div className="absolute top-0 right-0 w-32 h-32 bg-[#d006f9]/10 rounded-full blur-[40px] -translate-y-1/2 translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                
                                {/* Status Indicator (Top Right) */}
                                <div className="absolute top-6 right-6 z-10">
                                    <span className={cn(
                                        "text-[10px] font-bold px-3 py-1.5 rounded-full border flex items-center gap-1.5 uppercase tracking-widest shadow-sm",
                                        vehicle.aktif
                                            ? "bg-[#0df259]/10 text-[#0df259] border-[#0df259]/30 shadow-[0_0_10px_rgba(13,242,89,0.1)]"
                                            : "bg-white/5 text-white/50 border-white/10"
                                    )}>
                                        <span className={cn(
                                            "w-2 h-2 rounded-full",
                                            vehicle.aktif ? "bg-[#0df259] shadow-[0_0_5px_#0df259] animate-pulse" : "bg-white/30"
                                        )}></span>
                                        {vehicle.aktif ? 'AKTİF' : 'PASİF'}
                                    </span>
                                </div>

                                {/* Vehicle Header */}
                                <div className="flex items-start gap-4 mb-6 relative z-10">
                                    <div className="w-14 h-14 bg-black/60 border border-white/10 rounded-2xl flex items-center justify-center shrink-0 shadow-[inset_0_2px_4px_rgba(0,0,0,0.5)]">
                                        <Truck className="w-7 h-7 text-white/80" />
                                    </div>
                                    <div className="flex-1 min-w-0 pr-20">
                                        <div className="bg-black/80 text-white text-xs font-black tracking-widest px-2.5 py-1 rounded inline-flex items-center border border-white/20 mb-2 shadow-[0_4px_10px_rgba(0,0,0,0.5)]">
                                            {vehicle.plaka}
                                        </div>
                                        <h3 className="text-lg font-black text-white truncate group-hover:text-[#d006f9] transition-colors">
                                            {vehicle.marka} {vehicle.model}
                                        </h3>
                                    </div>
                                </div>

                                {/* Stats Grid */}
                                <div className="grid grid-cols-2 gap-3 mb-6 relative z-10">
                                    <div className="bg-black/30 border border-white/5 rounded-xl p-3 flex flex-col gap-1">
                                        <div className="flex items-center gap-1.5 text-white/40 mb-0.5">
                                            <Calendar className="w-3.5 h-3.5" />
                                            <span className="text-[10px] font-bold uppercase tracking-wider">Model Yılı</span>
                                        </div>
                                        <span className="text-sm font-bold text-white">{vehicle.yil}</span>
                                    </div>
                                    <div className="bg-black/30 border border-white/5 rounded-xl p-3 flex flex-col gap-1">
                                        <div className="flex items-center gap-1.5 text-white/40 mb-0.5">
                                            <Droplet className="w-3.5 h-3.5" />
                                            <span className="text-[10px] font-bold uppercase tracking-wider">Yakıt Kapasite</span>
                                        </div>
                                        <span className="text-sm font-bold text-white">{vehicle.kapasite?.toLocaleString('tr-TR') || '-'} L</span>
                                    </div>
                                    <div className="col-span-2 bg-black/30 border border-white/5 rounded-xl p-3 flex flex-col gap-1">
                                        <div className="flex items-center gap-1.5 text-white/40 mb-0.5">
                                            <Gauge className="w-3.5 h-3.5" />
                                            <span className="text-[10px] font-bold uppercase tracking-wider">Hedef Tüketim (L/100km)</span>
                                        </div>
                                        <span className="text-sm font-bold text-white">{vehicle.hedef_tuketim || '-'} L</span>
                                    </div>
                                </div>

                                <div className="flex-1" />

                                {/* Actions Footer */}
                                <div className="flex justify-between items-center pt-4 border-t border-[#d006f9]/20 relative z-10">
                                    <button
                                        onClick={() => onViewDetail(vehicle)}
                                        className="h-10 px-4 rounded-xl bg-[#d006f9]/10 text-[#d006f9] border border-[#d006f9]/20 hover:bg-[#d006f9]/20 hover:border-[#d006f9]/40 font-bold text-xs flex items-center gap-2 transition-all"
                                    >
                                        <Activity className="w-4 h-4" />
                                        İçgörüler
                                    </button>
                                    
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => onEdit(vehicle)}
                                            className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 text-white/60 hover:text-white hover:bg-white/10 flex items-center justify-center transition-all"
                                            title="Düzenle"
                                        >
                                            <Edit2 className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => vehicle.id && handleOptimisticDelete(vehicle)}
                                            disabled={!!vehicle.id && deletingIds.has(vehicle.id)}
                                            className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 hover:bg-red-500/20 hover:border-red-500/40 flex items-center justify-center transition-all disabled:opacity-50"
                                            title="Sil"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                </AnimatePresence>
            </div>
        </div>
    )
}
