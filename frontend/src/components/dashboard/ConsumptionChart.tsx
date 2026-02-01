import { useEffect, useState } from 'react'
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts'
import { motion } from 'framer-motion'
import { dashboardApi } from '../../services/api'
import { RefreshCw, AlertCircle, BarChart3 } from 'lucide-react'

// Ay adları haritası
const MONTH_NAMES: Record<string, string> = {
    '01': 'Oca', '02': 'Şub', '03': 'Mar', '04': 'Nis',
    '05': 'May', '06': 'Haz', '07': 'Tem', '08': 'Ağu',
    '09': 'Eyl', '10': 'Eki', '11': 'Kas', '12': 'Ara'
}

interface ChartData {
    name: string
    value: number
    fullMonth: string
}

// Fallback mock data (API'den veri yoksa)
const FALLBACK_DATA: ChartData[] = [
    { name: 'Oca', value: 12000, fullMonth: '2026-01' },
    { name: 'Şub', value: 13500, fullMonth: '2025-12' },
    { name: 'Mar', value: 12500, fullMonth: '2025-11' },
    { name: 'Nis', value: 16000, fullMonth: '2025-10' },
    { name: 'May', value: 14500, fullMonth: '2025-09' },
    { name: 'Haz', value: 19000, fullMonth: '2025-08' },
]

export function ConsumptionChart() {
    const [data, setData] = useState<ChartData[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // API'den veri çek
    const fetchData = async () => {
        setLoading(true)
        setError(null)
        try {
            const response = await dashboardApi.getConsumptionTrend()

            if (Array.isArray(response) && response.length > 0) {
                // API response: [{ month: "2026-01", consumption: 1234.5 }, ...]
                const chartData: ChartData[] = response
                    .slice(0, 6) // Son 6 ay
                    .map((item: { month: string; consumption: number }) => {
                        const monthPart = item.month.split('-')[1] || '01'
                        return {
                            name: MONTH_NAMES[monthPart] || monthPart,
                            value: Math.round(item.consumption),
                            fullMonth: item.month
                        }
                    })
                    .reverse() // Kronolojik sırala

                setData(chartData)
            } else {
                // API boş döndü, fallback kullan
                setData(FALLBACK_DATA)
            }
        } catch (err) {
            console.error('ConsumptionChart API error:', err)
            setError('Grafik verileri yüklenemedi')
            setData(FALLBACK_DATA) // Hata durumunda da fallback göster
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
    }, [])

    // Loading skeleton
    if (loading) {
        return (
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col h-[450px] card-premium p-8 relative overflow-hidden"
            >
                <div className="flex justify-between items-center mb-10">
                    <div className="space-y-2">
                        <div className="h-6 w-48 bg-neutral-200 rounded-lg animate-pulse" />
                        <div className="h-4 w-64 bg-neutral-100 rounded-lg animate-pulse" />
                    </div>
                    <div className="h-8 w-40 bg-neutral-100 rounded-2xl animate-pulse" />
                </div>
                <div className="flex-1 flex items-center justify-center">
                    <div className="flex flex-col items-center gap-3 text-neutral-400">
                        <RefreshCw className="w-8 h-8 animate-spin" />
                        <span className="text-sm font-medium">Grafik yükleniyor...</span>
                    </div>
                </div>
            </motion.div>
        )
    }

    return (
        <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="flex flex-col h-[450px] card-premium p-8 relative overflow-hidden"
        >
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-10 relative z-10">
                <div>
                    <h3 className="text-xl font-black text-brand-dark tracking-tight">Filo Tüketim Analitiği</h3>
                    <p className="text-xs font-bold text-neutral-400 mt-1 uppercase tracking-wider">Aylık yakıt verimliliği ve tüketim trendi</p>
                </div>

                <div className="flex items-center gap-3">
                    {/* Error indicator */}
                    {error && (
                        <button
                            onClick={fetchData}
                            className="flex items-center gap-2 text-[11px] font-bold text-warning bg-warning/10 px-3 py-2 rounded-xl border border-warning/20 hover:bg-warning/20 transition-all"
                        >
                            <AlertCircle className="w-3.5 h-3.5" />
                            Örnek Veri
                        </button>
                    )}

                    <div className="flex items-center gap-3 text-[11px] font-black uppercase tracking-widest text-primary bg-primary/5 px-4 py-2 rounded-2xl border border-primary/10 transition-all hover:bg-primary/10 cursor-default">
                        <span className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse shadow-[0_0_8px_rgba(37,99,235,0.5)]"></span>
                        Toplam Tüketim (Litre)
                    </div>
                </div>
            </div>

            {/* Empty state */}
            {data.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-neutral-400">
                    <BarChart3 className="w-16 h-16 mb-4 opacity-30" />
                    <p className="text-lg font-semibold">Henüz veri yok</p>
                    <p className="text-sm">Yakıt kayıtları girildikçe grafik oluşacak</p>
                </div>
            ) : (
                <div className="flex-1 w-full min-h-0 relative z-10">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart
                            data={data}
                            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                        >
                            <defs>
                                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                            <XAxis
                                dataKey="name"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: '#94A3B8', fontSize: 10, fontWeight: 700 }}
                                dy={15}
                            />
                            <YAxis
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: '#94A3B8', fontSize: 10, fontWeight: 700 }}
                                tickFormatter={(value) => `${(value / 1000).toFixed(1)}k`}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'rgba(30, 41, 59, 0.95)',
                                    backdropFilter: 'blur(8px)',
                                    borderRadius: '16px',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)',
                                    padding: '12px 16px'
                                }}
                                itemStyle={{ color: '#fff', fontSize: '13px', fontWeight: 'bold' }}
                                labelStyle={{ color: '#94A3B8', marginBottom: '8px', fontSize: '11px', fontWeight: '800', textTransform: 'uppercase' }}
                                formatter={(value: number | undefined) => [`${(value ?? 0).toLocaleString('tr-TR')} Litre`, 'Tüketim']}
                            />
                            <Area
                                type="monotone"
                                dataKey="value"
                                stroke="#2563EB"
                                strokeWidth={4}
                                fillOpacity={1}
                                fill="url(#colorValue)"
                                animationDuration={2000}
                                activeDot={{ r: 8, strokeWidth: 4, stroke: '#fff', fill: '#2563EB' }}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Background Decorative Grid */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl -z-0" />
        </motion.div>
    )
}
