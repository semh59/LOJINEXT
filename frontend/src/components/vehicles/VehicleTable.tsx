import { useState, useEffect } from 'react'
import { Vehicle } from '../../types'
import { Edit2, Trash2, Truck, Gauge, Calendar, Droplet, Activity } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '../../lib/utils'
import { SkeletonTable } from './SkeletonTable'
import { Badge } from '../ui/Badge'

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
            <div className="flex flex-col items-center justify-center p-16 text-center border border-dashed border-border rounded-[24px] bg-bg-elevated group">
                <div className="w-20 h-20 bg-surface rounded-2xl flex items-center justify-center mb-6 border border-border shadow-sm group-hover:scale-105 transition-transform duration-300">
                    <Truck className="w-10 h-10 text-secondary" />
                </div>
                <h3 className="text-xl font-bold text-primary mb-2 tracking-tight">Henüz Araç Eklenmemiş</h3>
                <p className="text-secondary max-w-sm text-sm font-medium">
                    Filo yönetimine başlamak için sağ üstteki butondan yeni bir araç ekleyerek operasyonlarınızı başlatın.
                </p>
            </div>
        )
    }

    return (
        <div className="w-full space-y-6">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-[18px] font-bold text-primary flex items-center gap-3 tracking-tight">
                    <div className="w-10 h-10 bg-surface border border-border rounded-xl flex items-center justify-center text-accent shadow-sm">
                        <Truck className="w-5 h-5" />
                    </div>
                    Filo Araçları
                </h2>
                <div className="text-sm font-bold text-secondary bg-surface px-4 py-2 rounded-xl border border-border shadow-sm">
                    Toplam: <span className="text-accent ml-1">{vehicles.filter(v => !deletedIds.has(v.id!)).length} Araç</span>
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
                                    "bg-surface border border-border rounded-[24px] p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow hover:border-accent flex flex-col relative overflow-hidden group",
                                    vehicle.id && deletingIds.has(vehicle.id) && "opacity-50 grayscale pointer-events-none"
                                )}
                            >
                                {/* Background glow effect on hover */}
                                <div className="absolute top-0 right-0 w-32 h-32 bg-accent/10 rounded-full blur-[40px] -translate-y-1/2 translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                
                                { /* Status Indicator (Top Right) */ }
                                <div className="absolute top-6 right-6 z-10">
                                    <Badge variant={vehicle.aktif ? 'success' : 'default'} pulse={vehicle.aktif} className="uppercase tracking-widest text-[10px]">
                                        {vehicle.aktif ? 'AKTİF' : 'PASİF'}
                                    </Badge>
                                </div>

                                {/* Vehicle Header */}
                                <div className="flex items-start gap-4 mb-6 relative z-10">
                                    <div className="w-14 h-14 bg-bg-elevated border border-border rounded-[16px] flex items-center justify-center shrink-0">
                                        <Truck className="w-7 h-7 text-secondary" />
                                    </div>
                                    <div className="flex-1 min-w-0 pr-20">
                                        <div className="bg-bg-elevated text-primary text-[11px] font-bold tracking-widest px-2.5 py-1 rounded inline-flex items-center border border-border mb-2 shadow-sm">
                                            {vehicle.plaka}
                                        </div>
                                        <h3 className="text-[16px] font-bold text-primary truncate group-hover:text-accent transition-colors tracking-tight">
                                            {vehicle.marka} {vehicle.model}
                                        </h3>
                                    </div>
                                </div>

                                {/* Stats Grid */}
                                <div className="grid grid-cols-2 gap-3 mb-6 relative z-10">
                                    <div className="bg-bg-elevated border border-border rounded-[12px] p-3 flex flex-col gap-1">
                                        <div className="flex items-center gap-1.5 text-secondary mb-0.5">
                                            <Calendar className="w-3.5 h-3.5" />
                                            <span className="text-[10px] font-bold uppercase tracking-wider">Model Yılı</span>
                                        </div>
                                        <span className="text-[14px] font-bold text-primary">{vehicle.yil}</span>
                                    </div>
                                    <div className="bg-bg-elevated border border-border rounded-[12px] p-3 flex flex-col gap-1">
                                        <div className="flex items-center gap-1.5 text-secondary mb-0.5">
                                            <Droplet className="w-3.5 h-3.5" />
                                            <span className="text-[10px] font-bold uppercase tracking-wider">Yakıt Kapasite</span>
                                        </div>
                                        <span className="text-[14px] font-bold text-primary">{vehicle.kapasite?.toLocaleString('tr-TR') || '-'} L</span>
                                    </div>
                                    <div className="col-span-2 bg-bg-elevated border border-border rounded-[12px] p-3 flex flex-col gap-1">
                                        <div className="flex items-center gap-1.5 text-secondary mb-0.5">
                                            <Gauge className="w-3.5 h-3.5" />
                                            <span className="text-[10px] font-bold uppercase tracking-wider">Hedef Tüketim (L/100km)</span>
                                        </div>
                                        <span className="text-[14px] font-bold text-primary">{vehicle.hedef_tuketim || '-'} L</span>
                                    </div>
                                </div>

                                <div className="flex-1" />

                                {/* Actions Footer */}
                                <div className="flex justify-between items-center pt-4 border-t border-border relative z-10">
                                    <button
                                        onClick={() => onViewDetail(vehicle)}
                                        className="h-10 px-4 rounded-[10px] bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20 hover:border-accent/40 font-bold text-xs flex items-center gap-2 transition-all"
                                    >
                                        <Activity className="w-4 h-4" />
                                        İçgörüler
                                    </button>
                                    
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => onEdit(vehicle)}
                                            className="w-10 h-10 rounded-[10px] bg-surface border border-border text-secondary hover:text-accent hover:bg-bg-elevated flex items-center justify-center transition-all"
                                            title="Düzenle"
                                        >
                                            <Edit2 className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => vehicle.id && handleOptimisticDelete(vehicle)}
                                            disabled={!!vehicle.id && deletingIds.has(vehicle.id)}
                                            className="w-10 h-10 rounded-[10px] bg-danger/10 border border-danger/20 text-danger hover:bg-danger/20 hover:border-danger/40 flex items-center justify-center transition-all disabled:opacity-50"
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
