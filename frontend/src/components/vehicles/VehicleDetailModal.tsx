import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Truck, Fuel, Route, TrendingUp, Calendar, Gauge } from 'lucide-react'
import { Vehicle, VehicleStats } from '../../types'
import { vehiclesApi } from '../../services/api'

interface VehicleDetailModalProps {
    isOpen: boolean
    onClose: () => void
    vehicle: Vehicle | null
}

export function VehicleDetailModal({ isOpen, onClose, vehicle }: VehicleDetailModalProps) {
    const [stats, setStats] = useState<VehicleStats | null>(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        if (isOpen && vehicle?.id) {
            fetchStats()
        }
    }, [isOpen, vehicle?.id])

    const fetchStats = async () => {
        if (!vehicle?.id) return
        setLoading(true)
        try {
            const data = await vehiclesApi.getStats(vehicle.id)
            setStats(data)
        } catch (error) {
            console.error('Stats fetch error:', error)
            // Fallback: sadece araç bilgilerini göster
            setStats({
                ...vehicle,
                toplam_sefer: 0,
                toplam_km: 0,
                ort_tuketim: 0
            } as VehicleStats)
        } finally {
            setLoading(false)
        }
    }

    if (!isOpen || !vehicle) return null

    const statCards = [
        {
            icon: <Route className="w-5 h-5" />,
            label: 'Toplam Sefer',
            value: stats?.toplam_sefer ?? '-',
            color: 'bg-blue-50 text-blue-600'
        },
        {
            icon: <Gauge className="w-5 h-5" />,
            label: 'Toplam Kilometre',
            value: stats?.toplam_km ? `${stats.toplam_km.toLocaleString('tr-TR')} km` : '-',
            color: 'bg-emerald-50 text-emerald-600'
        },
        {
            icon: <TrendingUp className="w-5 h-5" />,
            label: 'Ort. Tüketim',
            value: stats?.ort_tuketim ? `${stats.ort_tuketim.toFixed(1)} L/100km` : '-',
            color: 'bg-amber-50 text-amber-600'
        }
    ]

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    transition={{ duration: 0.2 }}
                    className="bg-white rounded-[32px] w-full max-w-2xl shadow-2xl overflow-hidden"
                >
                    {/* Header */}
                    <div className="relative bg-gradient-to-br from-primary to-primary-dark p-6 text-white">
                        <button
                            onClick={onClose}
                            className="absolute right-4 top-4 p-2 text-white/70 hover:text-white hover:bg-white/10 rounded-full transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>

                        <div className="flex items-center gap-4">
                            <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                                <Truck className="w-8 h-8" />
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold">{vehicle.marka} {vehicle.model}</h2>
                                <div className="flex items-center gap-3 mt-1">
                                    <span className="font-mono text-lg bg-white/20 px-3 py-0.5 rounded-lg">
                                        {vehicle.plaka}
                                    </span>
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${vehicle.aktif
                                            ? 'bg-emerald-400/20 text-emerald-100'
                                            : 'bg-red-400/20 text-red-100'
                                        }`}>
                                        {vehicle.aktif ? 'Aktif' : 'Pasif'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Stats Cards */}
                    <div className="p-6 border-b border-neutral-100">
                        <div className="grid grid-cols-3 gap-4">
                            {statCards.map((stat, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: index * 0.1 }}
                                    className="bg-neutral-50 rounded-2xl p-4 text-center"
                                >
                                    <div className={`w-10 h-10 ${stat.color} rounded-xl flex items-center justify-center mx-auto mb-2`}>
                                        {stat.icon}
                                    </div>
                                    <p className="text-xs text-neutral-500 font-medium">{stat.label}</p>
                                    <p className="text-lg font-bold text-neutral-900 mt-0.5">
                                        {loading ? (
                                            <span className="inline-block w-12 h-5 bg-neutral-200 rounded animate-pulse" />
                                        ) : stat.value}
                                    </p>
                                </motion.div>
                            ))}
                        </div>
                    </div>

                    {/* Details Grid */}
                    <div className="p-6 space-y-6">
                        {/* Temel Bilgiler */}
                        <div>
                            <h3 className="text-sm font-bold text-neutral-500 uppercase tracking-wider mb-3">
                                Temel Bilgiler
                            </h3>
                            <div className="grid grid-cols-2 gap-4">
                                <DetailItem icon={<Calendar />} label="Üretim Yılı" value={vehicle.yil?.toString()} />
                                <DetailItem icon={<Fuel />} label="Tank Kapasitesi" value={vehicle.tank_kapasitesi ? `${vehicle.tank_kapasitesi} L` : '-'} />
                                <DetailItem icon={<TrendingUp />} label="Hedef Tüketim" value={vehicle.hedef_tuketim ? `${vehicle.hedef_tuketim} L/100km` : '-'} />
                                <DetailItem icon={<Gauge />} label="Max Yük" value={vehicle.maks_yuk_kapasitesi_kg ? `${vehicle.maks_yuk_kapasitesi_kg.toLocaleString('tr-TR')} kg` : '-'} />
                            </div>
                        </div>

                        {/* Fizik Parametreleri */}
                        {(vehicle.bos_agirlik_kg || vehicle.hava_direnc_katsayisi || vehicle.motor_verimliligi) && (
                            <div>
                                <h3 className="text-sm font-bold text-neutral-500 uppercase tracking-wider mb-3">
                                    Fizik Parametreleri
                                </h3>
                                <div className="grid grid-cols-3 gap-3">
                                    <MiniStat label="Boş Ağırlık" value={vehicle.bos_agirlik_kg ? `${vehicle.bos_agirlik_kg.toLocaleString('tr-TR')} kg` : '-'} />
                                    <MiniStat label="Hava Direnci (Cd)" value={vehicle.hava_direnc_katsayisi?.toString() ?? '-'} />
                                    <MiniStat label="Ön Kesit" value={vehicle.on_kesit_alani_m2 ? `${vehicle.on_kesit_alani_m2} m²` : '-'} />
                                    <MiniStat label="Motor Verimi" value={vehicle.motor_verimliligi ? `%${(vehicle.motor_verimliligi * 100).toFixed(0)}` : '-'} />
                                    <MiniStat label="Lastik Direnci" value={vehicle.lastik_direnc_katsayisi?.toString() ?? '-'} />
                                </div>
                            </div>
                        )}

                        {/* Notlar */}
                        {vehicle.notlar && (
                            <div>
                                <h3 className="text-sm font-bold text-neutral-500 uppercase tracking-wider mb-2">
                                    Notlar
                                </h3>
                                <p className="text-neutral-600 text-sm bg-neutral-50 rounded-xl p-4">
                                    {vehicle.notlar}
                                </p>
                            </div>
                        )}
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    )
}

// Helper components
function DetailItem({ icon, label, value }: { icon: React.ReactNode; label: string; value?: string }) {
    return (
        <div className="flex items-center gap-3 p-3 bg-neutral-50 rounded-xl">
            <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center text-neutral-400 shadow-sm">
                {icon}
            </div>
            <div>
                <p className="text-xs text-neutral-500">{label}</p>
                <p className="font-semibold text-neutral-900">{value || '-'}</p>
            </div>
        </div>
    )
}

function MiniStat({ label, value }: { label: string; value: string }) {
    return (
        <div className="bg-neutral-50 rounded-xl p-3 text-center">
            <p className="text-xs text-neutral-500">{label}</p>
            <p className="font-bold text-neutral-800 mt-0.5">{value}</p>
        </div>
    )
}
