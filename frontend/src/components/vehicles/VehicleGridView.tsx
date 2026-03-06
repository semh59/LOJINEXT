import { Vehicle } from '../../types'
import { VehicleCard } from './VehicleCard'

import { Truck } from 'lucide-react'

interface VehicleGridViewProps {
    vehicles: Vehicle[]
    loading: boolean
    onEdit: (vehicle: Vehicle) => void
    onDelete: (vehicle: Vehicle) => void
    onViewDetail: (vehicle: Vehicle) => void
}

export function VehicleGridView({ vehicles, loading, onEdit, onDelete, onViewDetail }: VehicleGridViewProps) {
    if (loading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="glass-card border border-white/5 p-6 h-[320px] animate-pulse">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-14 h-14 rounded-2xl bg-white/5" />
                            <div className="space-y-2">
                                <div className="h-4 w-24 bg-white/5 rounded" />
                                <div className="h-3 w-16 bg-white/5 rounded" />
                            </div>
                        </div>
                        <div className="h-12 w-full bg-white/5 rounded-xl mb-6" />
                        <div className="grid grid-cols-2 gap-3">
                            <div className="h-16 bg-white/5 rounded-2xl" />
                            <div className="h-16 bg-white/5 rounded-2xl" />
                        </div>
                    </div>
                ))}
            </div>
        )
    }

    if (vehicles.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-20 text-center glass-card border border-white/5">
                <div className="w-24 h-24 bg-white/5 rounded-full flex items-center justify-center mb-6 shadow-xl border border-white/10">
                    <Truck className="w-12 h-12 text-slate-500" />
                </div>
                <h3 className="text-2xl font-black text-white tracking-tight">Henüz Araç Eklenmemiş</h3>
                <p className="text-slate-400 mt-2 max-w-sm font-medium">
                    Filo yönetimine başlamak için sağ üstteki butondan yeni bir araç ekleyin veya Excel yükleyin.
                </p>
            </div>
        )
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {vehicles.map((vehicle) => (
                <VehicleCard
                    key={vehicle.id}
                    vehicle={vehicle}
                    onEdit={onEdit}
                    onDelete={onDelete}
                    onViewDetail={onViewDetail}
                />
            ))}
        </div>
    )
}
