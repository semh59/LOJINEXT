import { Truck, Eye, Edit2, Trash2, Calendar, Fuel, Target } from 'lucide-react'
import { Vehicle } from '../../types'
import { DropdownMenu } from '../ui/DropdownMenu'

interface VehicleCardProps {
    vehicle: Vehicle
    onEdit: (vehicle: Vehicle) => void
    onDelete: (vehicle: Vehicle) => void
    onViewDetail: (vehicle: Vehicle) => void
}

export function VehicleCard({ vehicle, onEdit, onDelete, onViewDetail }: VehicleCardProps) {
    return (
        <div
            className={`group relative bg-white rounded-[32px] border border-neutral-200 p-6 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 ${!vehicle.aktif ? 'opacity-75 grayscale-[0.5]' : ''}`}
        >
            {/* Header / Brand */}
            <div className="flex justify-between items-start mb-6">
                <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20 group-hover:scale-110 transition-transform duration-300">
                        <Truck className="w-7 h-7" />
                    </div>
                    <div>
                        <h3 className="text-lg font-black text-neutral-900 tracking-tight leading-none mb-1">
                            {vehicle.marka}
                        </h3>
                        <p className="text-sm text-neutral-500 font-bold uppercase tracking-wider">
                            {vehicle.model}
                        </p>
                    </div>
                </div>

                <DropdownMenu
                    align="right"
                    items={[
                        {
                            label: 'Düzenle',
                            icon: <Edit2 className="w-4 h-4" />,
                            onClick: () => onEdit(vehicle)
                        },
                        {
                            label: 'Detaylar',
                            icon: <Eye className="w-4 h-4" />,
                            onClick: () => onViewDetail(vehicle)
                        },
                        {
                            label: 'Sil',
                            icon: <Trash2 className="w-4 h-4" />,
                            onClick: () => onDelete(vehicle),
                            variant: 'danger'
                        }
                    ]}
                />
            </div>

            {/* Plate Badge */}
            <div className="mb-6">
                <span className="font-mono text-lg font-black tracking-widest bg-neutral-100 text-neutral-800 px-4 py-2 rounded-xl border-2 border-dashed border-neutral-300 block text-center shadow-inner group-hover:border-primary/30 group-hover:bg-primary/5 transition-colors">
                    {vehicle.plaka}
                </span>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-3">
                <div className="bg-neutral-50 rounded-2xl p-3 flex flex-col gap-1 border border-neutral-100">
                    <div className="flex items-center gap-1.5 text-neutral-400">
                        <Calendar className="w-3.5 h-3.5" />
                        <span className="text-[10px] font-bold uppercase tracking-tighter">Model Yılı</span>
                    </div>
                    <span className="text-sm font-black text-neutral-700">{vehicle.yil || '---'}</span>
                </div>

                <div className="bg-neutral-50 rounded-2xl p-3 flex flex-col gap-1 border border-neutral-100">
                    <div className="flex items-center gap-1.5 text-neutral-400">
                        <Fuel className="w-3.5 h-3.5" />
                        <span className="text-[10px] font-bold uppercase tracking-tighter">Tank Kapasite</span>
                    </div>
                    <span className="text-sm font-black text-neutral-700">
                        {vehicle.tank_kapasitesi}<span className="text-[10px] ml-0.5 text-neutral-400">L</span>
                    </span>
                </div>

                <div className="col-span-2 bg-gradient-to-br from-neutral-50 to-neutral-100/50 rounded-2xl p-3 flex items-center justify-between border border-neutral-100">
                    <div className="flex items-center gap-2 text-neutral-400">
                        <Target className="w-4 h-4" />
                        <span className="text-[10px] font-bold uppercase tracking-tighter">Hedef Tüketim</span>
                    </div>
                    <span className="text-sm font-black text-primary">
                        {vehicle.hedef_tuketim}<span className="text-[10px] ml-0.5 opacity-60">L/100km</span>
                    </span>
                </div>
            </div>

            {/* Status Indicator */}
            <div className="mt-6 flex items-center justify-between">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border ${vehicle.aktif
                    ? 'bg-emerald-50 text-emerald-600 border-emerald-100'
                    : 'bg-amber-50 text-amber-600 border-amber-100'
                    }`}>
                    <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${vehicle.aktif ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
                    {vehicle.aktif ? 'Aktif' : 'Pasif'}
                </span>

                <button
                    onClick={() => onViewDetail(vehicle)}
                    className="text-xs font-bold text-primary hover:text-primary-dark tracking-tight flex items-center gap-1 transition-colors"
                >
                    Detayları Gör
                </button>
            </div>
        </div>
    )
}
