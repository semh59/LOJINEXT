import { useState } from 'react'
import { motion } from 'framer-motion'
import { MainLayout } from '../components/layout/MainLayout'
import { PredictionForm } from '../components/predictions/PredictionForm'
import { PredictionResultCard } from '../components/predictions/PredictionResultCard'
import { PredictionChart } from '../components/predictions/PredictionChart'
import { TrendAnalysisCard } from '../components/predictions/TrendAnalysisCard'
import { predictionsApi } from '../services/api'
import { PredictionResult, PredictionRequest } from '../types'
import { Sparkles } from 'lucide-react'
import { useNotify } from '../context/NotificationContext'

export default function PredictionsPage() {
    const { notify } = useNotify()
    const [result, setResult] = useState<PredictionResult | null>(null)
    const [loading, setLoading] = useState(false)
    const [selectedVehicleId, setSelectedVehicleId] = useState<number | undefined>(undefined)

    const handlePredict = async (data: PredictionRequest) => {
        setLoading(true)
        try {
            const res = await predictionsApi.predict(data)
            setResult(res)
            setSelectedVehicleId(data.arac_id)
            notify('success', 'Tahmin Tamamlandı', `Tahmini tüketim: ${res.tahmini_tuketim.toFixed(1)} L/100km`)
        } catch (error) {
            console.error('Tahmin hatası:', error)
            notify('error', 'Tahmin Hatası', 'Yakıt tahmini yapılamadı. Lütfen tekrar deneyin.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <MainLayout title="AI Tahmin" breadcrumb="Sistem / Tahmin">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
                {/* Header */}
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-indigo-600 rounded-2xl shadow-lg shadow-indigo-500/30 text-white">
                        <Sparkles className="w-8 h-8" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-black text-brand-dark tracking-tighter mb-1">
                            Yapay Zeka Tahmin
                        </h1>
                        <p className="text-neutral-500 font-medium">Gelecek seferler için tüketim ve maliyet öngörüleri.</p>
                    </div>
                </div>

                {/* Main Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    {/* Left Column: Form + Charts */}
                    <div className="lg:col-span-7 space-y-8">
                        <PredictionForm onPredict={handlePredict} isLoading={loading} />

                        {/* Charts Row */}
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                            <PredictionChart selectedVehicleId={selectedVehicleId} />
                            <TrendAnalysisCard selectedVehicleId={selectedVehicleId} />
                        </div>
                    </div>

                    {/* Right Column: Result */}
                    <div className="lg:col-span-5">
                        <PredictionResultCard result={result} />
                    </div>
                </div>
            </motion.div>
        </MainLayout>
    )
}
