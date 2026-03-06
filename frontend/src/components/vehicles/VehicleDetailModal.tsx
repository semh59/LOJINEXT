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
                ort_tuketim: 0,
                toplam_yol: 0,
                ortalama_tuketim: 0,
                aktif_gun: 0
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
            color: 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
        },
        {
            icon: <Gauge className="w-5 h-5" />,
            label: 'Toplam Kilometre',
            value: stats?.toplam_km ? `${stats.toplam_km.toLocaleString('tr-TR')} km` : '-',
            color: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
        },
        {
            icon: <TrendingUp className="w-5 h-5" />,
            label: 'Ort. Tüketim',
            value: stats?.ort_tuketim ? `${Number(stats.ort_tuketim).toFixed(1)} L/100km` : '-',
            color: 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
        }
    ]

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    transition={{ duration: 0.2 }}
                    className="bg-[#1a0121]/90 backdrop-blur-xl rounded-[32px] w-full max-w-2xl border border-[#d006f9]/30 shadow-[0_0_40px_rgba(208,6,249,0.15)] overflow-hidden flex flex-col max-h-[90vh]"
                >
                    {/* Header */}
                    <div className="relative bg-black/40 p-6 border-b border-[#d006f9]/20 shrink-0">
                        <button
                            onClick={onClose}
                            className="absolute right-4 top-4 p-2 text-white/50 hover:text-white hover:bg-white/10 rounded-full transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>

                        <div className="flex items-center gap-4">
                            <div className="w-16 h-16 bg-[#d006f9]/20 border border-[#d006f9]/40 rounded-2xl flex items-center justify-center shadow-[0_0_15px_rgba(208,6,249,0.3)]">
                                <Truck className="w-8 h-8 text-[#d006f9]" />
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-white">{vehicle.marka} {vehicle.model}</h2>
                                <div className="flex items-center gap-3 mt-1">
                                    <span className="font-mono text-lg bg-black/50 border border-white/10 px-3 py-0.5 rounded-lg text-white/90">
                                        {vehicle.plaka}
                                    </span>
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold border flex items-center gap-1.5 ${vehicle.aktif
                                            ? 'bg-[#0df259]/10 text-[#0df259] border-[#0df259]/30'
                                            : 'bg-white/5 text-white/50 border-white/10'
                                        }`}>
                                        <span className={`w-1.5 h-1.5 rounded-full ${vehicle.aktif ? 'bg-[#0df259] shadow-[0_0_5px_#0df259] animate-pulse' : 'bg-white/30'}`}></span>
                                        {vehicle.aktif ? 'Aktif' : 'Pasif'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="overflow-y-auto custom-scrollbar flex-1 p-6 space-y-6">
                        {/* Stats Cards */}
                        <div className="grid grid-cols-3 gap-4">
                            {statCards.map((stat, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: index * 0.1 }}
                                    className="bg-black/30 border border-white/5 rounded-2xl p-4 text-center hover:bg-black/50 transition-colors"
                                >
                                    <div className={`w-10 h-10 ${stat.color} rounded-xl flex items-center justify-center mx-auto mb-2`}>
                                        {stat.icon}
                                    </div>
                                    <p className="text-xs text-white/50 font-medium">{stat.label}</p>
                                    <p className="text-lg font-bold text-white mt-0.5">
                                        {loading ? (
                                            <span className="inline-block w-12 h-5 bg-white/10 rounded animate-pulse" />
                                        ) : stat.value}
                                    </p>
                                </motion.div>
                            ))}
                        </div>

                        {/* Details Grid */}
                        <div className="space-y-6">
                            {/* Temel Bilgiler */}
                            <div>
                                <h3 className="text-sm font-bold text-white/40 uppercase tracking-widest mb-3">
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
                                    <h3 className="text-sm font-bold text-white/40 uppercase tracking-widest mb-3">
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
                                    <h3 className="text-sm font-bold text-white/40 uppercase tracking-widest mb-2">
                                        Notlar
                                    </h3>
                                    <p className="text-white/70 text-sm bg-black/40 border border-white/5 rounded-xl p-4">
                                        {vehicle.notlar}
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    )
}

// Helper components
function DetailItem({ icon, label, value }: { icon: React.ReactNode; label: string; value?: string }) {
    return (
        <div className="flex items-center gap-3 p-3 bg-black/30 border border-white/5 rounded-xl hover:bg-black/50 transition-colors">
            <div className="w-8 h-8 bg-black/50 border border-white/10 rounded-lg flex items-center justify-center text-[#d006f9]/80 shadow-sm">
                {icon}
            </div>
            <div>
                <p className="text-xs text-white/50">{label}</p>
                <p className="font-semibold text-white/90">{value || '-'}</p>
            </div>
        </div>
    )
}

function MiniStat({ label, value }: { label: string; value: string }) {
    return (
        <div className="bg-black/30 border border-white/5 rounded-xl p-3 text-center transition-colors hover:bg-black/50">
            <p className="text-xs text-white/50">{label}</p>
            <p className="font-bold text-white/90 mt-0.5">{value}</p>
        </div>
    )
}
