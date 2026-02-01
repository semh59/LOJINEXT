import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MainLayout } from '../components/layout/MainLayout'
import { ReportCards } from '../components/reports/ReportCards'
import { CostAnalysisChart } from '../components/reports/CostAnalysisChart'
import { ROICalculator } from '../components/reports/ROICalculator'
import { reportsApi } from '../services/api'
import { CostAnalysis } from '../types'
import { useNotify } from '../context/NotificationContext'
import { FileText, PieChart, TrendingUp } from 'lucide-react'
import { cn } from '../lib/utils'

export default function ReportsPage() {
    const { notify } = useNotify()
    const [activeTab, setActiveTab] = useState<'pdf' | 'cost' | 'roi'>('pdf')
    const [costData, setCostData] = useState<CostAnalysis[]>([])
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        if (activeTab === 'cost' && costData.length === 0) {
            setLoading(true)
            reportsApi.getCostAnalysis()
                .then(setCostData)
                .catch(console.error)
                .finally(() => setLoading(false))
        }
    }, [activeTab])

    const handleDownload = async (type: string) => {
        notify('info', 'Hazırlanıyor...', 'Rapor oluşturuluyor, lütfen bekleyin.')
        try {
            await reportsApi.downloadPdf(type)
            notify('success', 'İndirildi', 'Rapor başarıyla indirildi.')
        } catch {
            notify('error', 'Hata', 'Rapor oluşturulamadı.')
        }
    }

    const tabs = [
        { id: 'pdf', label: 'PDF Raporlar', icon: FileText },
        { id: 'cost', label: 'Maliyet Analizi', icon: PieChart },
        { id: 'roi', label: 'Tasarruf & ROI', icon: TrendingUp },
    ]

    return (
        <MainLayout title="Raporlar" breadcrumb="Sistem / Raporlar">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
                <div>
                    <h1 className="text-3xl font-black text-brand-dark tracking-tighter mb-2">Detaylı Raporlar</h1>
                    <p className="text-neutral-500 font-medium">Filo performans raporları, maliyet analizleri ve yatırım simülasyonları.</p>
                </div>

                {/* Custom Tab Navigation */}
                <div className="flex p-1 bg-white/50 backdrop-blur-md border border-white/20 rounded-2xl w-fit">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={cn(
                                "flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all relative overflow-hidden",
                                activeTab === tab.id ? "text-white shadow-lg shadow-brand-dark/20" : "text-neutral-500 hover:text-neutral-700 hover:bg-white/40"
                            )}
                        >
                            {activeTab === tab.id && (
                                <motion.div
                                    layoutId="activeTab"
                                    className="absolute inset-0 bg-brand-dark"
                                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                                />
                            )}
                            <span className="relative z-10 flex items-center gap-2">
                                <tab.icon className="w-4 h-4" />
                                {tab.label}
                            </span>
                        </button>
                    ))}
                </div>

                <div className="relative min-h-[500px]">
                    <AnimatePresence mode="wait">
                        {activeTab === 'pdf' && (
                            <motion.div
                                key="pdf"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                transition={{ duration: 0.3 }}
                            >
                                <ReportCards onDownload={handleDownload} />
                            </motion.div>
                        )}

                        {activeTab === 'cost' && (
                            <motion.div
                                key="cost"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                transition={{ duration: 0.3 }}
                            >
                                {loading ? (
                                    <div className="flex items-center justify-center h-64 text-neutral-400">Yükleniyor...</div>
                                ) : (
                                    <CostAnalysisChart data={costData} />
                                )}
                            </motion.div>
                        )}

                        {activeTab === 'roi' && (
                            <motion.div
                                key="roi"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                transition={{ duration: 0.3 }}
                            >
                                <ROICalculator />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </motion.div>
        </MainLayout>
    )
}
