import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { PremiumLayout } from '../components/layout/PremiumLayout'
import { ReportCards } from '../components/reports/ReportCards'
import { CostAnalysisChart } from '../components/reports/CostAnalysisChart'
import { ROICalculator } from '../components/reports/ROICalculator'
import { reportsApi } from '../services/api'
import { useNotify } from '../context/NotificationContext'
import { FileText, PieChart, TrendingUp } from 'lucide-react'
import { cn } from '../lib/utils'
import { ExportDialog, ExportType, ExportConfig } from '../components/shared/ExportDialog'

export default function ReportsPage() {
    const { notify } = useNotify()
    const [activeTab, setActiveTab] = useState<'pdf' | 'cost' | 'roi'>('pdf')
    // Export Dialog State
    const [isExportDialogOpen, setIsExportDialogOpen] = useState(false)
    const [exportType, setExportType] = useState<ExportType>('fleet_summary')
    const [exportTitle, setExportTitle] = useState('')
    const [exportDescription, setExportDescription] = useState('')

    // React Query for Cost Analysis
    const { data: costData = [], isLoading: costLoading } = useQuery({
        queryKey: ['costAnalysis'],
        queryFn: () => reportsApi.getCostAnalysis(),
        enabled: activeTab === 'cost',
        staleTime: 10 * 60 * 1000, // 10 minutes cache
    })

    const handleDownloadClick = async (type: string) => {
        const titleMap: Record<string, string> = {
            'fleet_summary': 'Filo Özeti',
            'vehicle_detail': 'Araç Raporu',
            'driver_comparison': 'Sürücü Karşılaştırma'
        }
        const descMap: Record<string, string> = {
            'fleet_summary': 'Tüm filonun genel performans verilerini içerir.',
            'vehicle_detail': 'Belirli bir aracın sefer ve tüketim detaylarını analiz eder.',
            'driver_comparison': 'Sürücülerin performans, tüketim ve ihlal verilerini karşılaştırır.'
        }

        setExportType(type === 'vehicle_detail' ? 'vehicle_report' : type as ExportType)
        setExportTitle(titleMap[type] || 'Rapor İndir')
        setExportDescription(descMap[type] || 'Kapsam ve format seçin.')
        setIsExportDialogOpen(true)
    }

    const handleExportConfirm = async (config: ExportConfig) => {
        try {
            const { format, startDate, endDate, targetId, month, year } = config
            
            let blob: Blob;
            let filename = `rapor_${exportType}_${new Date().toISOString().split('T')[0]}`

            if (format === 'pdf') {
                const params: Record<string, any> = { 
                    start_date: startDate, 
                    end_date: endDate,
                    month: month,
                    year: year
                }
                blob = await reportsApi.downloadPdf(exportType === 'vehicle_report' ? 'vehicle_detail' : exportType, targetId ? Number(targetId) : undefined, params)
                filename += '.pdf'
            } else {
                const params: Record<string, any> = { 
                    start_date: startDate, 
                    end_date: endDate,
                    months: 12
                }
                blob = await reportsApi.downloadExcel(exportType === 'vehicle_report' ? 'fleet_summary' : exportType, params)
                filename += '.xlsx'
            }
            
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = filename
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
            
            notify('success', 'Hazır', 'Rapor başarıyla indirildi.')
        } catch (err: any) {
            console.error(err)
            notify('error', 'Hata', err.message || 'Rapor oluşturulamadı.')
            throw err
        }
    }

    const tabs = [
        { id: 'pdf', label: 'PDF Raporlar', icon: FileText },
        { id: 'cost', label: 'Maliyet Analizi', icon: PieChart },
        { id: 'roi', label: 'Tasarruf & ROI', icon: TrendingUp },
    ]

    return (
        <PremiumLayout title="Sistem Analizi & Raporlar">
            <div className="flex-1 overflow-y-auto p-4 lg:p-8 space-y-8">
                <div className="space-y-1">
                    <h1 className="text-3xl font-black text-primary tracking-tighter">Detaylı Raporlar</h1>
                    <p className="text-secondary font-medium">Filo performans raporları, maliyet analizleri ve yatırım simülasyonları.</p>
                </div>

                {/* Custom Tab Navigation */}
                <div className="flex p-1 bg-surface border border-border rounded-xl w-fit shadow-sm">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={cn(
                                "flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-bold transition-all relative overflow-hidden",
                                activeTab === tab.id ? "text-primary shadow-sm" : "text-secondary hover:text-primary hover:bg-bg-elevated"
                            )}
                        >
                            {activeTab === tab.id && (
                                <motion.div
                                    layoutId="activeTabIndicator"
                                    className="absolute inset-0 bg-bg-elevated rounded-lg border border-border shadow-sm"
                                    transition={{ type: "spring", bounce: 0.2, duration: 0.2 }}
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
                                    <ReportCards onDownload={handleDownloadClick} />
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
                                {costLoading ? (
                                    <div className="flex items-center justify-center h-64 text-secondary">Yükleniyor...</div>
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
            </div>

            <ExportDialog 
                isOpen={isExportDialogOpen}
                onClose={() => setIsExportDialogOpen(false)}
                type={exportType}
                title={exportTitle}
                description={exportDescription}
                onExport={handleExportConfirm}
            />
        </PremiumLayout>
    )
}
