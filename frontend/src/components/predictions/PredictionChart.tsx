import { useState, useEffect } from 'react'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip } from 'recharts'
import { motion } from 'framer-motion'
import { predictionsApi } from '../../services/api'
import { ForecastResult } from '../../types'
import { Loader2, AlertCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface PredictionChartProps {
    selectedVehicleId?: number
}

interface ChartData {
    date: string
    val: number
    low: number
    high: number
}

export function PredictionChart({ selectedVehicleId }: PredictionChartProps) {
    const [data, setData] = useState<ChartData[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [trend, setTrend] = useState<'increasing' | 'stable' | 'decreasing'>('stable')

    useEffect(() => {
        const loadForecast = async () => {
            setLoading(true)
            setError(null)
            try {
                const result: ForecastResult = await predictionsApi.getForecast(selectedVehicleId)

                if (result.success && result.forecast && result.forecast_dates) {
                    const chartData: ChartData[] = result.forecast_dates.map((date, i) => ({
                        date: formatDate(date),
                        val: result.forecast[i],
                        low: result.confidence_low?.[i] ?? result.forecast[i] * 0.9,
                        high: result.confidence_high?.[i] ?? result.forecast[i] * 1.1
                    }))
                    setData(chartData)
                    setTrend(result.trend || 'stable')
                } else {
                    // Fallback: API çalışmıyorsa mock data
                    setData(getMockData())
                    setTrend('stable')
                }
            } catch (err) {
                console.error('Forecast yüklenemedi:', err)
                setError('Tahmin verisi yüklenemedi')
                setData(getMockData())
            } finally {
                setLoading(false)
            }
        }

        loadForecast()
    }, [selectedVehicleId])

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr)
        const days = ['Paz', 'Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt']
        return days[date.getDay()]
    }

    const getMockData = (): ChartData[] => [
        { date: 'Pzt', val: 28.5, low: 26.0, high: 31.0 },
        { date: 'Sal', val: 29.2, low: 26.5, high: 31.9 },
        { date: 'Çar', val: 27.8, low: 25.2, high: 30.4 },
        { date: 'Per', val: 30.1, low: 27.4, high: 32.8 },
        { date: 'Cum', val: 28.9, low: 26.2, high: 31.6 },
        { date: 'Cmt', val: 26.5, low: 24.0, high: 29.0 },
        { date: 'Paz', val: 25.8, low: 23.3, high: 28.3 },
    ]

    const TrendIcon = trend === 'increasing' ? TrendingUp : trend === 'decreasing' ? TrendingDown : Minus
    const trendColor = trend === 'increasing' ? 'text-red-500' : trend === 'decreasing' ? 'text-green-500' : 'text-neutral-500'
    const trendText = trend === 'increasing' ? 'Artıyor' : trend === 'decreasing' ? 'Azalıyor' : 'Sabit'

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="w-full h-[300px] glass p-6 rounded-[32px] border border-white/50"
        >
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-black text-brand-dark">7 Günlük Tahmin</h3>
                <div className={`flex items-center gap-1.5 text-sm font-bold ${trendColor} bg-white/50 px-2 py-1 rounded-full`}>
                    <TrendIcon className="w-4 h-4" />
                    <span>{trendText}</span>
                </div>
            </div>

            {loading ? (
                <div className="flex items-center justify-center h-[200px]">
                    <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                </div>
            ) : error ? (
                <div className="flex flex-col items-center justify-center h-[200px] text-red-500">
                    <AlertCircle className="w-8 h-8 mb-2" />
                    <p className="text-sm">{error}</p>
                </div>
            ) : (
                <ResponsiveContainer width="100%" height="80%">
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1} />
                                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                        <XAxis
                            dataKey="date"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#64748B', fontSize: 12, fontWeight: 600 }}
                            dy={10}
                        />
                        <YAxis hide domain={['dataMin - 5', 'dataMax + 5']} />
                        <RechartsTooltip
                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' }}
                            cursor={{ stroke: '#6366f1', strokeWidth: 2 }}
                            formatter={(value, name) => {
                                if (value === undefined || value === null) return ['--', '']
                                const numValue = typeof value === 'number' ? value : parseFloat(String(value))
                                const label = name === 'val' ? 'Tahmin' : name === 'low' ? 'Alt Sınır' : 'Üst Sınır'
                                return [`${numValue.toFixed(1)} L/100km`, label]
                            }}
                        />
                        {/* Güven Aralığı (Confidence Band) */}
                        <Area
                            type="monotone"
                            dataKey="high"
                            stroke="transparent"
                            fill="url(#colorConfidence)"
                        />
                        <Area
                            type="monotone"
                            dataKey="low"
                            stroke="transparent"
                            fill="transparent"
                        />
                        {/* Ana Tahmin Çizgisi */}
                        <Area
                            type="monotone"
                            dataKey="val"
                            stroke="#6366f1"
                            strokeWidth={3}
                            fillOpacity={1}
                            fill="url(#colorVal)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            )}
        </motion.div>
    )
}
