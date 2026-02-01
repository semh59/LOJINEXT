import { useState, useEffect } from 'react'
import { RoiStats } from '../../types'
import { motion } from 'framer-motion'
import { PiggyBank, TrendingUp, Target } from 'lucide-react'
import { reportsApi } from '@/services/api'

export function ROICalculator() {
    const [investment, setInvestment] = useState(50000)
    const [stats, setStats] = useState<RoiStats | null>(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        const fetchRoi = async () => {
            setLoading(true)
            try {
                const data = await reportsApi.getRoiStats(investment)
                setStats(data)
            } catch (error) {
                console.error(error)
            } finally {
                setLoading(false)
            }
        }
        // Debounce simple implementation
        const timer = setTimeout(fetchRoi, 500)
        return () => clearTimeout(timer)
    }, [investment])

    const formatCurrency = (val: number) =>
        new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(val)

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Input Section */}
            <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: loading ? 0.5 : 1, x: 0 }}
                className="glass p-8 rounded-[32px] border border-white/50 space-y-8"
            >
                <div>
                    <h3 className="text-xl font-black text-brand-dark mb-2">Yatırım Simülasyonu</h3>
                    <p className="text-neutral-500 text-sm">Sisteme yapılacak yatırım tutarını belirleyerek potansiyel kazancınızı hesaplayın.</p>
                </div>

                <div className="space-y-4">
                    <div className="flex justify-between items-center text-sm font-bold">
                        <span className="text-neutral-600">Yatırım Tutarı</span>
                        <span className="text-primary">{formatCurrency(investment)}</span>
                    </div>
                    <input
                        type="range"
                        min="10000"
                        max="500000"
                        step="5000"
                        value={investment}
                        onChange={(e) => setInvestment(Number(e.target.value))}
                        className="w-full h-2 bg-neutral-100 rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                    <div className="flex justify-between text-xs text-neutral-400 font-bold uppercase">
                        <span>10k ₺</span>
                        <span>500k ₺</span>
                    </div>
                </div>

                <div className="p-6 bg-blue-50/50 rounded-2xl border border-blue-100/50">
                    <div className="flex items-start gap-3">
                        <Target className="w-5 h-5 text-blue-600 mt-1" />
                        <div>
                            <h4 className="font-bold text-blue-900 text-sm mb-1">Hedef Tüketim</h4>
                            <p className="text-blue-700/80 text-xs">
                                Mevcut ortalama <b>{stats?.current_consumption} L/100km</b> üzerinden,
                                AI desteği ile <b>{stats?.target_consumption} L/100km</b> hedeflenmektedir.
                            </p>
                        </div>
                    </div>
                </div>
            </motion.div>

            {/* Results Section */}
            <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
            >
                <div className="glass p-8 rounded-[32px] border border-white/50 flex items-center justify-between relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="relative z-10">
                        <p className="text-xs font-black uppercase text-neutral-400 mb-1">Yıllık Tasarruf</p>
                        <h3 className="text-3xl font-black text-emerald-600">{stats ? formatCurrency(stats.annual_savings) : '-'}</h3>
                    </div>
                    <div className="w-12 h-12 bg-emerald-100 rounded-2xl flex items-center justify-center text-emerald-600">
                        <PiggyBank className="w-6 h-6" />
                    </div>
                </div>

                <div className="glass p-8 rounded-[32px] border border-white/50 flex items-center justify-between relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="relative z-10">
                        <p className="text-xs font-black uppercase text-neutral-400 mb-1">ROI (Yatırım Getirisi)</p>
                        <h3 className="text-3xl font-black text-purple-600">%{stats ? stats.roi_percentage.toFixed(0) : '-'}</h3>
                    </div>
                    <div className="w-12 h-12 bg-purple-100 rounded-2xl flex items-center justify-center text-purple-600">
                        <TrendingUp className="w-6 h-6" />
                    </div>
                </div>

                {stats && stats.roi_percentage > 100 && (
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="p-4 bg-gradient-to-r from-brand-dark to-slate-900 rounded-2xl text-white text-center shadow-xl shadow-brand-dark/20"
                    >
                        <p className="text-sm font-bold">🚀 Harika Yatırım! 12 aydan kısa sürede amorti ediyor.</p>
                    </motion.div>
                )}
            </motion.div>
        </div>
    )
}
