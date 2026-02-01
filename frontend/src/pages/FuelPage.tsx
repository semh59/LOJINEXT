
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { MainLayout } from '../components/layout/MainLayout'
import { fuelApi, vehiclesApi } from '../services/api'
import { FuelTable } from '../components/fuel/FuelTable'
import { FuelModal } from '../components/fuel/FuelModal'
import { FuelStats } from '../components/fuel/FuelStats'
import { FuelRecord, FuelStats as IFuelStats } from '../types'
import { useNotify } from '../context/NotificationContext'
import { Plus, Upload, Filter, Calendar } from 'lucide-react'
import { cn } from '../lib/utils'

export default function FuelPage() {
    const { notify } = useNotify()
    const [records, setRecords] = useState<FuelRecord[]>([])
    const [stats, setStats] = useState<IFuelStats>({ total_consumption: 0, total_cost: 0, avg_consumption: 0, avg_price: 0 })
    const [loading, setLoading] = useState(true)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [selectedRecord, setSelectedRecord] = useState<FuelRecord | null>(null)
    const [isFilterOpen, setIsFilterOpen] = useState(false)

    // Filter State
    const [startDate, setStartDate] = useState(new Date(new Date().setMonth(new Date().getMonth() - 1)).toISOString().slice(0, 10))
    const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10))
    const [vehicleFilter, setVehicleFilter] = useState('')
    const [vehicles, setVehicles] = useState<any[]>([])

    useEffect(() => {
        vehiclesApi.getAll({ limit: 100 }).then(setVehicles).catch(() => { })
    }, [])

    const fetchData = async () => {
        setLoading(true)
        try {
            const [data, statsData] = await Promise.all([
                fuelApi.getAll({
                    baslangic_tarih: startDate,
                    bitis_tarih: endDate,
                    arac_id: vehicleFilter ? Number(vehicleFilter) : undefined,
                    limit: 100
                }),
                fuelApi.getStats({
                    baslangic_tarih: startDate,
                    bitis_tarih: endDate
                })
            ])
            setRecords(Array.isArray(data) ? data : [])
            setStats(statsData)
        } catch (error) {
            console.error(error)
            notify('error', 'Hata', 'Veriler yüklenemedi.')
            // Fallback mock data
            if (records.length === 0) {
                const mock: FuelRecord[] = [
                    { id: 1, tarih: '2026-01-25', arac_id: 1, plaka: '34ABC123', istasyon: 'Shell Maslak', litre: 450, birim_fiyat: 42.50, toplam_tutar: 19125, km_sayac: 45000, depo_durumu: 'Doldu', durum: 'Bekliyor' },
                    { id: 2, tarih: '2026-01-24', arac_id: 2, plaka: '06DEF456', istasyon: 'Opet Ankara', litre: 380, birim_fiyat: 41.80, toplam_tutar: 15884, km_sayac: 62000, depo_durumu: 'Kısmi', durum: 'Onaylandı' },
                ]
                setRecords(mock)
                setStats({ total_consumption: 24500, total_cost: 896500, avg_consumption: 28.5, avg_price: 41.90 })
            }
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
    }, [startDate, endDate, vehicleFilter])

    return (
        <MainLayout title="Yakıt Yönetimi" breadcrumb="Sistem / Yakıt">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 relative z-10">
                    <div>
                        <motion.h1 className="text-3xl font-black text-brand-dark tracking-tighter mb-2">
                            Yakıt Takibi
                        </motion.h1>
                        <p className="text-neutral-500 font-medium">Filo yakıt tüketimi ve maliyet analizi.</p>
                    </div>

                    <div className="flex items-center gap-3">
                        <button className="btn btn-secondary shadow-soft">
                            <Upload className="w-4 h-4 rotate-180" />
                            Dışa Aktar
                        </button>
                        <button
                            onClick={() => { setSelectedRecord(null); setIsModalOpen(true) }}
                            className="btn btn-primary"
                        >
                            <Plus className="w-5 h-5" />
                            Yeni Yakıt Kaydı
                        </button>
                    </div>
                </div>

                {/* Stats Cards */}
                <FuelStats stats={stats} loading={loading} />

                {/* Filters */}
                <div className="glass p-2 rounded-2xl flex flex-wrap gap-2 items-center border border-white/50 relative z-10">
                    <div className="flex items-center gap-2 px-3 py-2 bg-white/50 rounded-xl">
                        <Calendar className="w-4 h-4 text-neutral-400" />
                        <input
                            type="date"
                            value={startDate}
                            onChange={e => setStartDate(e.target.value)}
                            className="text-xs font-bold text-neutral-600 bg-transparent outline-none"
                        />
                        <span className="text-neutral-300">-</span>
                        <input
                            type="date"
                            value={endDate}
                            onChange={e => setEndDate(e.target.value)}
                            className="text-xs font-bold text-neutral-600 bg-transparent outline-none"
                        />
                    </div>

                    <div className="h-8 w-px bg-neutral-200/50 mx-2" />

                    <select
                        value={vehicleFilter}
                        onChange={e => setVehicleFilter(e.target.value)}
                        className="h-10 px-4 rounded-xl bg-white/50 text-xs font-bold text-neutral-600 outline-none hover:bg-white transition-colors cursor-pointer border-transparent focus:border-primary/20 border"
                    >
                        <option value="">Tüm Araçlar</option>
                        {vehicles.map(v => (
                            <option key={v.id} value={v.id}>{v.plaka}</option>
                        ))}
                    </select>

                    <div className="ml-auto">
                        <button
                            onClick={() => setIsFilterOpen(!isFilterOpen)}
                            className={cn(
                                "p-2 rounded-xl transition-all",
                                isFilterOpen ? "bg-brand-dark text-white" : "hover:bg-neutral-100 text-neutral-500"
                            )}
                        >
                            <Filter className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Table */}
                <div className="glass rounded-[32px] border border-white/50 overflow-hidden shadow-xl shadow-black/5 relative z-0">
                    <FuelTable
                        records={records}
                        loading={loading}
                        onEdit={(r) => { setSelectedRecord(r); setIsModalOpen(true) }}
                        onDelete={async (r) => {
                            if (!window.confirm('Bu kaydı silmek istediğinize emin misiniz?')) return
                            try {
                                await fuelApi.delete(r.id!)
                                notify('success', 'Başarılı', 'Kayıt silindi')
                                fetchData()
                            } catch { notify('error', 'Hata', 'Silinemedi') }
                        }}
                    />
                </div>
            </motion.div>

            <FuelModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                record={selectedRecord}
                onSave={async (data) => {
                    if (selectedRecord?.id) {
                        await fuelApi.update(selectedRecord.id, data)
                        notify('success', 'Güncellendi', 'Kayıt başarıyla güncellendi.')
                    } else {
                        await fuelApi.create(data)
                        notify('success', 'Eklendi', 'Yeni yakıt kaydı eklendi.')
                    }
                    fetchData()
                }}
            />
        </MainLayout>
    )
}
