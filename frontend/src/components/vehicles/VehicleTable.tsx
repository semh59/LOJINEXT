import { useState, useEffect } from 'react'
import { Vehicle } from '../../types'
import { Edit2, Trash2, Truck, Eye } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { DropdownMenu } from '../ui/DropdownMenu'
import { SkeletonTable } from './SkeletonTable'

interface VehicleTableProps {
    vehicles: Vehicle[]
    loading: boolean
    onEdit: (vehicle: Vehicle) => void
    onDelete: (id: number) => Promise<void>
    onViewDetail: (vehicle: Vehicle) => void
}

export function VehicleTable({ vehicles, loading, onEdit, onDelete, onViewDetail }: VehicleTableProps) {
    // Optimistic delete için state
    const [deletingIds, setDeletingIds] = useState<Set<number>>(new Set())
    const [deletedIds, setDeletedIds] = useState<Set<number>>(new Set())

    // Veri değiştiğinde (örn: fetch'ten sonra) optimistic state'i temizle
    useEffect(() => {
        setDeletedIds(new Set())
        setDeletingIds(new Set())
    }, [vehicles])

    // Optimistic delete handler
    const handleOptimisticDelete = async (id: number) => {
        // Hemen UI'dan kaldır (optimistic)
        setDeletedIds(prev => new Set([...prev, id]))
        setDeletingIds(prev => new Set([...prev, id]))

        try {
            await onDelete(id)
            // Başarılı - kalıcı olarak kaldır
        } catch (error) {
            // Hata - geri getir (rollback)
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

    // Skeleton loading göster
    if (loading) {
        return <SkeletonTable rows={5} />
    }

    // Boş durum
    if (vehicles.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-center border-2 border-dashed border-neutral-200 rounded-3xl bg-neutral-50/50">
                <div className="w-16 h-16 bg-neutral-100 rounded-full flex items-center justify-center mb-4">
                    <Truck className="w-8 h-8 text-neutral-400" />
                </div>
                <h3 className="text-lg font-bold text-neutral-900">Henüz Araç Eklenmemiş</h3>
                <p className="text-neutral-500 mt-1 max-w-sm">
                    Filo yönetimine başlamak için sağ üstteki butondan yeni bir araç ekleyin.
                </p>
            </div>
        )
    }

    // Silinen araçları filtrele (optimistic)
    const visibleVehicles = vehicles.filter(v => v.id && !deletedIds.has(v.id))

    return (
        <div className="overflow-hidden rounded-[24px] border border-neutral-200 bg-white shadow-sm">
            <table className="w-full">
                <thead>
                    <tr className="bg-neutral-50 border-b border-neutral-100">
                        <th className="px-4 py-4 text-left text-xs font-bold text-neutral-500 uppercase tracking-wider w-[180px]">Araç</th>
                        <th className="px-4 py-4 text-left text-xs font-bold text-neutral-500 uppercase tracking-wider w-[130px]">Plaka</th>
                        <th className="px-4 py-4 text-center text-xs font-bold text-neutral-500 uppercase tracking-wider w-[70px]">Yıl</th>
                        <th className="px-4 py-4 text-right text-xs font-bold text-neutral-500 uppercase tracking-wider w-[90px]">Tank</th>
                        <th className="px-4 py-4 text-right text-xs font-bold text-neutral-500 uppercase tracking-wider w-[100px]">Hedef</th>
                        <th className="px-4 py-4 text-center text-xs font-bold text-neutral-500 uppercase tracking-wider w-[90px]">Durum</th>
                        <th className="px-4 py-4 text-center text-xs font-bold text-neutral-500 uppercase tracking-wider w-[70px]">İşlemler</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                    <AnimatePresence mode="popLayout">
                        {visibleVehicles.map((vehicle, index) => (
                            <motion.tr
                                key={vehicle.id}
                                layout
                                initial={{ opacity: 0, y: 10 }}
                                animate={{
                                    opacity: deletingIds.has(vehicle.id!) ? 0.5 : 1,
                                    y: 0,
                                    x: 0
                                }}
                                exit={{
                                    opacity: 0,
                                    x: -100,
                                    transition: { duration: 0.2 }
                                }}
                                transition={{ delay: index * 0.03, duration: 0.2 }}
                                className="group hover:bg-blue-50/30 transition-colors"
                            >
                                {/* Araç (Marka + Model) */}
                                <td className="px-4 py-3">
                                    <div className="flex items-center gap-2">
                                        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center text-blue-600 shadow-sm shrink-0">
                                            <Truck className="w-4 h-4" />
                                        </div>
                                        <div className="min-w-0">
                                            <p className="font-bold text-brand-dark text-sm truncate">{vehicle.marka}</p>
                                            <p className="text-xs text-neutral-500 font-medium truncate">{vehicle.model}</p>
                                        </div>
                                    </div>
                                </td>

                                {/* Plaka */}
                                <td className="px-4 py-3">
                                    <span className="font-mono bg-neutral-100 px-2 py-0.5 rounded text-neutral-700 text-xs font-bold border border-neutral-200">
                                        {vehicle.plaka}
                                    </span>
                                </td>

                                {/* Yıl */}
                                <td className="px-4 py-3 text-sm text-neutral-600 font-semibold text-center">
                                    {vehicle.yil}
                                </td>

                                {/* Tank Kapasitesi */}
                                <td className="px-4 py-3 text-right">
                                    <span className="text-sm font-semibold text-neutral-700">
                                        {vehicle.tank_kapasitesi || '-'}
                                        {vehicle.tank_kapasitesi && <span className="text-neutral-400 ml-0.5 text-xs">L</span>}
                                    </span>
                                </td>

                                {/* Hedef Tüketim */}
                                <td className="px-4 py-3 text-right">
                                    <span className="text-sm font-semibold text-neutral-700">
                                        {vehicle.hedef_tuketim || '-'}
                                        {vehicle.hedef_tuketim && <span className="text-neutral-400 ml-0.5 text-xs">L/100km</span>}
                                    </span>
                                </td>

                                {/* Durum Badge */}
                                <td className="px-4 py-3 text-center">
                                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${vehicle.aktif
                                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                        : 'bg-amber-50 text-amber-700 border border-amber-200'
                                        }`}>
                                        <span className={`w-1.5 h-1.5 rounded-full mr-1 ${vehicle.aktif ? 'bg-emerald-500' : 'bg-amber-500'
                                            }`} />
                                        {vehicle.aktif ? 'Aktif' : 'Pasif'}
                                    </span>
                                </td>

                                {/* Actions Dropdown */}
                                <td className="px-4 py-3 text-center">
                                    <DropdownMenu
                                        align="right"
                                        items={[
                                            {
                                                label: 'Düzenle',
                                                icon: <Edit2 className="w-4 h-4" />,
                                                onClick: () => onEdit(vehicle)
                                            },
                                            {
                                                label: 'Detay',
                                                icon: <Eye className="w-4 h-4" />,
                                                onClick: () => onViewDetail(vehicle)
                                            },
                                            {
                                                label: 'Sil',
                                                icon: <Trash2 className="w-4 h-4" />,
                                                onClick: () => vehicle.id && handleOptimisticDelete(vehicle.id),
                                                variant: 'danger'
                                            }
                                        ]}
                                    />
                                </td>
                            </motion.tr>
                        ))}
                    </AnimatePresence>
                </tbody>
            </table>
        </div>
    )
}
