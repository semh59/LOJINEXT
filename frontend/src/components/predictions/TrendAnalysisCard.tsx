import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { predictionsApi } from '../../services/api'
import { TrendAnalysis } from '../../types'
import { TrendingUp, TrendingDown, Minus, Loader2, BarChart3 } from 'lucide-react'

interface TrendAnalysisCardProps {
    selectedVehicleId?: number
    days?: number
}

export function TrendAnalysisCard({ selectedVehicleId, days = 30 }: TrendAnalysisCardProps) {
    const [trend, setTrend] = useState<TrendAnalysis | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const loadTrend = async () => {
            setLoading(true)
            setError(null)
            try {
                const result = await predictionsApi.getTrend(selectedVehicleId, days)
                if (result.success) {
                    setTrend(result)
                } else {
                    setError('Trend verisi alınamadı')
                }
            } catch (err) {
                console.error('Trend yüklenemedi:', err)
                setError('Trend analizi yüklenemedi')
            } finally {
                setLoading(false)
            }
        }

        loadTrend()
    }, [selectedVehicleId, days])

    if (loading) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass p-6 rounded-[24px] border border-white/50 flex items-center justify-center h-[200px]"
            >
                <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            </motion.div>
        )
    }

    if (error || !trend) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass p-6 rounded-[24px] border border-white/50"
            >
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-slate-100 rounded-xl">
                        <BarChart3 className="w-5 h-5 text-slate-400" />
                    </div>
                    <h3 className="text-lg font-bold text-brand-dark">Trend Analizi</h3>
                </div>
                <p className="text-sm text-neutral-500">Trend verisi yüklenemedi. Yeterli veri olmayabilir.</p>
            </motion.div>
        )
    }

    const TrendIcon = trend.trend === 'increasing' ? TrendingUp : trend.trend === 'decreasing' ? TrendingDown : Minus
    const trendColor = trend.trend === 'increasing' ? 'text-red-500 bg-red-50' : trend.trend === 'decreasing' ? 'text-green-500 bg-green-50' : 'text-neutral-500 bg-neutral-100'
    const trendBadgeColor = trend.trend === 'increasing' ? 'bg-red-100 text-red-700' : trend.trend === 'decreasing' ? 'bg-green-100 text-green-700' : 'bg-neutral-100 text-neutral-700'

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass p-6 rounded-[24px] border border-white/50"
        >
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-xl ${trendColor}`}>
                        <TrendIcon className="w-5 h-5" />
                    </div>
                    <h3 className="text-lg font-bold text-brand-dark">Trend Analizi</h3>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-bold ${trendBadgeColor}`}>
                    {trend.trend_tr}
                </span>
            </div>

            <div className="space-y-4">
                {/* Eğim */}
                <div className="flex justify-between items-center">
                    <span className="text-sm text-neutral-600">Eğim</span>
                    <span className={`text-sm font-bold ${trend.slope > 0 ? 'text-red-500' : trend.slope < 0 ? 'text-green-500' : 'text-neutral-500'}`}>
                        {trend.slope > 0 ? '+' : ''}{trend.slope.toFixed(2)}
                    </span>
                </div>

                {/* Mevcut Ortalama */}
                <div className="flex justify-between items-center">
                    <span className="text-sm text-neutral-600">Mevcut Ortalama</span>
                    <span className="text-sm font-bold text-brand-dark">{trend.current_avg.toFixed(1)} L/100km</span>
                </div>

                {/* Önceki Ortalama */}
                <div className="flex justify-between items-center">
                    <span className="text-sm text-neutral-600">Önceki Ortalama</span>
                    <span className="text-sm font-bold text-neutral-500">{trend.previous_avg.toFixed(1)} L/100km</span>
                </div>

                {/* Değişim */}
                <div className="pt-3 border-t border-neutral-100">
                    <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-neutral-600">Değişim</span>
                        <span className={`text-lg font-black ${trend.current_avg > trend.previous_avg ? 'text-red-500' : 'text-green-500'}`}>
                            {((trend.current_avg - trend.previous_avg) / trend.previous_avg * 100).toFixed(1)}%
                        </span>
                    </div>
                </div>
            </div>
        </motion.div>
    )
}
