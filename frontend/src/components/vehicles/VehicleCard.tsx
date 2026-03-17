import { Truck, Eye, Edit2, Trash2, Calendar, Fuel, Gauge } from 'lucide-react'
import { Vehicle } from '../../types'
import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'

interface VehicleCardProps {
    vehicle: Vehicle
    onEdit: (vehicle: Vehicle) => void
    onDelete: (vehicle: Vehicle) => void
    onViewDetail: (vehicle: Vehicle) => void
}

export function VehicleCard({ vehicle, onEdit, onDelete, onViewDetail }: VehicleCardProps) {
    // Note: kilometre data might come from vehicle stats enrichment
    const displayedKm = (vehicle as any).kilometre || (vehicle as any).toplam_km || 0

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card-premium h-full flex flex-col p-6 group"
        >
            {/* Header Area */}
            <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-accent/10 rounded-[22px] flex items-center justify-center border border-accent/20 transition-transform group-hover:scale-110 group-hover:rotate-3 shadow-lg">
                        <Truck className="w-7 h-7 text-accent" />
                    </div>
                    <div>
                        <h3 className="text-xl font-black text-primary leading-tight uppercase tracking-tight">{vehicle.plaka}</h3>
                        <p className="text-xs font-bold text-secondary uppercase tracking-widest">{vehicle.marka} {vehicle.model}</p>
                    </div>
                </div>

                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                        onClick={() => onEdit(vehicle)}
                        className="p-2.5 rounded-xl hover:bg-bg-elevated text-secondary hover:text-accent transition-all"
                    >
                        <Edit2 className="w-4.5 h-4.5" />
                    </button>
                    <button
                        onClick={() => onDelete(vehicle)}
                        className="p-2.5 rounded-xl hover:bg-danger/10 text-secondary hover:text-danger transition-all"
                    >
                        <Trash2 className="w-4.5 h-4.5" />
                    </button>
                </div>
            </div>

            {/* Main Info */}
            <div className="grid grid-cols-2 gap-3 mb-6">
                <div className="bg-bg-elevated rounded-2xl p-4 border border-border shadow-inner">
                    <div className="flex items-center gap-2 text-secondary mb-1">
                        <Calendar className="w-3.5 h-3.5" />
                        <span className="text-[10px] font-bold uppercase tracking-wider">Model Yılı</span>
                    </div>
                    <span className="text-sm font-extrabold text-primary">{vehicle.yil}</span>
                </div>
                <div className="bg-bg-elevated rounded-2xl p-4 border border-border shadow-inner">
                    <div className="flex items-center gap-2 text-secondary mb-1">
                        <Gauge className="w-3.5 h-3.5" />
                        <span className="text-[10px] font-bold uppercase tracking-wider">Kilometre</span>
                    </div>
                    <span className="text-sm font-extrabold text-primary">
                        {displayedKm.toLocaleString('tr-TR')} <span className="text-[10px] text-secondary">km</span>
                    </span>
                </div>
            </div>

            {/* Performance Stats */}
            <div className="space-y-3 flex-1">
                <div className="flex items-center justify-between px-1">
                    <div className="flex items-center gap-2 text-secondary">
                        <Fuel className="w-4 h-4" />
                        <span className="text-xs font-bold uppercase tracking-tighter">Ort. Tüketim</span>
                    </div>
                    <span className={cn(
                        "text-sm font-black",
                        (vehicle as any).ort_tuketim > vehicle.hedef_tuketim ? "text-danger" : "text-success"
                    )}>
                        {Number((vehicle as any).ort_tuketim || 0).toFixed(1)} <span className="text-[10px] opacity-60">L/100km</span>
                    </span>
                </div>
                {/* Comparison to Target */}
                <div className="px-1 flex justify-between text-[10px] text-secondary font-medium">
                    <span>Hedef: {vehicle.hedef_tuketim} L</span>
                    <span className={cn(
                        (vehicle as any).ort_tuketim > vehicle.hedef_tuketim ? "text-danger/80" : "text-success/80"
                    )}>
                        {((vehicle as any).ort_tuketim && vehicle.hedef_tuketim) 
                            ? `${(((vehicle as any).ort_tuketim - vehicle.hedef_tuketim) / vehicle.hedef_tuketim * 100).toFixed(0)}%` 
                            : '-'}
                    </span>
                </div>
                <div className="w-full h-1.5 bg-bg-elevated rounded-full overflow-hidden">
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: '65%' }} // Mock value or calculate based on performance
                        className="h-full bg-accent shadow-sm shadow-accent/20"
                    />
                </div>
            </div>

            {/* Footer */}
            <div className="mt-8 pt-6 border-t border-border flex items-center justify-between">
                <div className={cn(
                    "px-3 py-1 rounded-xl text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 border",
                    vehicle.aktif
                        ? "bg-success/10 text-success border-success/20"
                        : "bg-warning/10 text-warning border-warning/20"
                )}>
                    <div className={cn("w-2 h-2 rounded-full", vehicle.aktif ? "bg-success shadow-sm animate-pulse" : "bg-warning")} />
                    {vehicle.aktif ? 'Aktif' : 'Pasif'}
                </div>

                <button
                    onClick={() => onViewDetail(vehicle)}
                    className="h-10 px-4 rounded-xl text-xs font-bold text-accent bg-accent/5 hover:bg-accent hover:text-bg-base transition-all flex items-center gap-2"
                >
                    <Eye className="w-3.5 h-3.5" /> Detaylar
                </button>
            </div>
        </motion.div>
    )
}
