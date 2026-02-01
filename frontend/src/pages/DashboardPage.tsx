import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { MainLayout } from '../components/layout/MainLayout'
import { StatsCard } from '../components/dashboard/StatsCard'
import { ConsumptionChart } from '../components/dashboard/ConsumptionChart'
import { Modal } from '../components/ui/Modal'
import { NewTripStepper } from '../components/trips/NewTripStepper'
import { FuelModal } from '../components/fuel/FuelModal'
import { dashboardApi, tripsApi, fuelApi, reportsApi } from '../services/api'
import { MOCK_DASHBOARD_STATS } from '../services/mockData'
import { DashboardStats, Trip, FuelRecord } from '../types'
import { useNotify } from '../context/NotificationContext'
import {
    Truck,
    MapPin,
    Fuel,
    Plus,
    ArrowRight,
    Users,
    Calendar,
    Gauge,
    Download,
    FileText
} from 'lucide-react'
import { cn } from '../lib/utils'

const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
}

const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
}

export default function DashboardPage() {
    const { notify } = useNotify()
    const [stats, setStats] = useState<DashboardStats | null>(null)
    const [loading, setLoading] = useState(true)

    // Modal states
    const [tripModalOpen, setTripModalOpen] = useState(false)
    const [fuelModalOpen, setFuelModalOpen] = useState(false)
    const [reportLoading, setReportLoading] = useState(false)

    useEffect(() => {
        let mounted = true
        async function loadData() {
            setLoading(true)
            try {
                const data = await dashboardApi.getStats()
                if (mounted) {
                    setStats({
                        ...data,
                        // Ensure required fields for StatsCard if they renamed in backend
                        toplam_sefer: data.toplam_sefer || 0,
                        toplam_km: data.toplam_km || 0,
                        toplam_yakit: data.toplam_yakit || 0,
                        trends: data.trends || { sefer: 0, km: 0, tuketim: 0 }
                    })
                }
            } catch (error) {
                console.error('Failed to load dashboard stats', error)
                notify('error', 'Veri Hatası', 'Gerçek zamanlı veriler alınamadı, örnek veriler gösteriliyor.')
                if (mounted) setStats(MOCK_DASHBOARD_STATS)
            } finally {
                if (mounted) setLoading(false)
            }
        }
        loadData()
        return () => { mounted = false }
    }, [])

    // Quick action handlers
    const handleNewTrip = async (tripData: Partial<Trip>) => {
        try {
            await tripsApi.create(tripData)
            notify('success', 'Başarılı', 'Yeni sefer kaydedildi!')
            setTripModalOpen(false)
        } catch (error) {
            notify('error', 'Hata', 'Sefer kaydedilemedi.')
        }
    }

    const handleNewFuel = async (fuelData: Partial<FuelRecord>) => {
        try {
            await fuelApi.create(fuelData)
            notify('success', 'Başarılı', 'Yakıt kaydı eklendi!')
            setFuelModalOpen(false)
        } catch (error) {
            notify('error', 'Hata', 'Yakıt kaydı eklenemedi.')
        }
    }

    const handleDownloadReport = async () => {
        setReportLoading(true)
        try {
            await reportsApi.downloadPdf('dashboard', {})
            notify('success', 'Hazırlanıyor', 'Rapor indirilmeye başlandı.')
        } catch (error) {
            notify('error', 'Hata', 'Rapor indirilemedi.')
        } finally {
            setReportLoading(false)
        }
    }

    // Quick actions configuration
    const quickActions = [
        {
            label: 'Yeni Sefer Kaydı',
            icon: Plus,
            color: 'text-primary',
            onClick: () => setTripModalOpen(true)
        },
        {
            label: 'Yakıt Verisi Gir',
            icon: Fuel,
            color: 'text-success',
            onClick: () => setFuelModalOpen(true)
        },
        {
            label: 'Rapor İndir',
            icon: Download,
            color: 'text-warning',
            onClick: handleDownloadReport,
            loading: reportLoading
        },
    ]

    return (
        <MainLayout title="Genel Özet" breadcrumb="Sistem / Panel">
            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="space-y-10"
            >
                {/* 4 Cards Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                    <StatsCard
                        index={0}
                        label="Toplam Sefer"
                        value={loading ? '-' : stats?.toplam_sefer?.toLocaleString() ?? '-'}
                        icon={Truck}
                        iconColor="blue"
                        isLoading={loading}
                        trend={loading ? undefined : `${(stats?.trends?.sefer ?? 0) > 0 ? '+' : ''}${stats?.trends?.sefer ?? 0}%`}
                        trendDirection={loading ? 'neutral' : ((stats?.trends?.sefer ?? 0) > 0 ? 'up' : (stats?.trends?.sefer ?? 0) < 0 ? 'down' : 'neutral')}
                    />
                    <StatsCard
                        index={1}
                        label="Toplam Mesafe"
                        value={loading ? '-' : `${stats?.toplam_km?.toLocaleString() ?? '-'} km`}
                        icon={MapPin}
                        iconColor="green"
                        isLoading={loading}
                        trend={loading ? undefined : `${(stats?.trends?.km ?? 0) > 0 ? '+' : ''}${stats?.trends?.km ?? 0}%`}
                        trendDirection={loading ? 'neutral' : ((stats?.trends?.km ?? 0) > 0 ? 'up' : (stats?.trends?.km ?? 0) < 0 ? 'down' : 'neutral')}
                    />
                    <StatsCard
                        index={2}
                        label="Toplam Yakıt"
                        value={loading ? '-' : `${stats?.toplam_yakit?.toLocaleString() ?? '-'} L`}
                        icon={Fuel}
                        iconColor="red"
                        isLoading={loading}
                        trend={loading ? undefined : `${(stats?.trends?.tuketim ?? 0) > 0 ? '+' : ''}${stats?.trends?.tuketim ?? 0}%`}
                        trendDirection={loading ? 'neutral' : ((stats?.trends?.tuketim ?? 0) > 0 ? 'up' : (stats?.trends?.tuketim ?? 0) < 0 ? 'down' : 'neutral')}
                    />
                    <StatsCard
                        index={3}
                        label="Filo Verimliliği"
                        value={loading ? '-' : `${stats?.filo_ortalama ?? '-'} L/100km`}
                        icon={Gauge}
                        iconColor="purple"
                        isLoading={loading}
                        trend="Sabit"
                        trendDirection="neutral"
                    />
                </div>

                {/* 3 Cards Row */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <StatsCard
                        index={4}
                        label="Aktif Araç"
                        value={loading ? '-' : stats?.aktif_arac?.toLocaleString() ?? '-'}
                        icon={Truck}
                        iconColor="blue"
                        isLoading={loading}
                    />
                    <StatsCard
                        index={5}
                        label="Aktif Şoför"
                        value={loading ? '-' : stats?.aktif_sofor?.toLocaleString() ?? '-'}
                        icon={Users}
                        iconColor="orange"
                        isLoading={loading}
                    />
                    <StatsCard
                        index={6}
                        label="Bugünkü Sefer"
                        value={loading ? '-' : stats?.bugun_sefer?.toLocaleString() ?? '-'}
                        icon={Calendar}
                        iconColor="green"
                        isLoading={loading}
                    />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Ana Grafik */}
                    <div className="lg:col-span-2">
                        <ConsumptionChart />
                    </div>

                    {/* Yan Panel (Hızlı İşlemler) */}
                    <div className="flex flex-col gap-6">
                        {/* Quick Actions Card */}
                        <motion.div
                            variants={itemVariants}
                            className="card-premium p-8 relative overflow-hidden group"
                        >
                            <h3 className="text-xl font-black text-brand-dark mb-6 tracking-tight">Hızlı Erişim</h3>
                            <div className="space-y-4">
                                {quickActions.map((action, idx) => (
                                    <button
                                        key={idx}
                                        onClick={action.onClick}
                                        disabled={action.loading}
                                        className="w-full flex items-center justify-between p-4 bg-neutral-100/50 hover:bg-white rounded-[20px] transition-all duration-300 group/btn border border-transparent hover:border-primary/20 hover:shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-wait"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className={cn("w-10 h-10 rounded-2xl bg-white flex items-center justify-center shadow-soft transition-transform group-hover/btn:rotate-12", action.color)}>
                                                {action.loading ? (
                                                    <FileText className="w-5 h-5 animate-pulse" />
                                                ) : (
                                                    <action.icon className="w-5 h-5" />
                                                )}
                                            </div>
                                            <span className="font-bold text-neutral-700">{action.label}</span>
                                        </div>
                                        <ArrowRight className="w-4 h-4 text-neutral-300 group-hover/btn:text-primary group-hover/btn:translate-x-1 transition-all" />
                                    </button>
                                ))}
                            </div>
                        </motion.div>
                    </div>
                </div>
            </motion.div>

            {/* New Trip Modal */}
            <Modal
                isOpen={tripModalOpen}
                onClose={() => setTripModalOpen(false)}
                title="Yeni Sefer Oluştur"
                size="lg"
            >
                <NewTripStepper
                    onComplete={handleNewTrip}
                    onCancel={() => setTripModalOpen(false)}
                />
            </Modal>

            {/* Fuel Entry Modal */}
            <FuelModal
                isOpen={fuelModalOpen}
                onClose={() => setFuelModalOpen(false)}
                onSave={handleNewFuel}
            />
        </MainLayout>
    )
}

