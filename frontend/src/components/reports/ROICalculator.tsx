import { useState, useEffect } from 'react'
import { RoiStats } from '../../types'
import { motion } from 'framer-motion'
import { PiggyBank, TrendingUp, Target } from 'lucide-react'
import { reportsApi } from '@/services/api'

export function ROICalculator() {
    const [investment, setInvestment] = useState(50000)
    const [stats, setStats] = useState<RoiStats | null>(null)
    const [loading, setLoading] = useState(false)
    const [savings, setSavings] = useState<{ potential_savings: number; savings_percentage: number } | null>(null)

    useEffect(() => {
        const fetchRoi = async () => {
            setLoading(true)
            try {
                const [roiData, savingsData] = await Promise.all([
                    reportsApi.getRoiStats(investment),
                    reportsApi.getSavingsPotential(28) // Target 28 L/100km
                ])
                setStats(roiData)
                setSavings(savingsData)
            } catch (error) {
                console.error(error)
            } finally {
                setLoading(false)
            }
        }
        // ... (rest of the debounce)
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
                className="bg-surface p-6 lg:p-8 rounded-2xl border border-border shadow-sm space-y-8"
            >
                <div>
                    <h3 className="text-xl font-bold text-primary mb-2">Yatırım Simülasyonu</h3>
                    <p className="text-secondary text-sm">Sisteme yapılacak yatırım tutarını belirleyerek potansiyel kazancınızı hesaplayın.</p>
                </div>

                <div className="space-y-4">
                    <div className="flex justify-between items-center text-sm font-bold">
                        <span className="text-secondary">Yatırım Tutarı</span>
                        <span className="text-primary">{formatCurrency(investment)}</span>
                    </div>
                    <input
                        type="range"
                        min="10000"
                        max="500000"
                        step="5000"
                        value={investment}
                        onChange={(e) => setInvestment(Number(e.target.value))}
                        className="w-full h-2 bg-border rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                    <div className="flex justify-between text-xs text-secondary font-bold uppercase">
                        <span>10k ₺</span>
                        <span>500k ₺</span>
                    </div>
                </div>

                <div className="p-6 bg-info/10 rounded-2xl border border-info/20">
                    <div className="flex items-start gap-3">
                        <Target className="w-5 h-5 text-info mt-1" />
                        <div>
                            <h4 className="font-bold text-info text-sm mb-1">Hedef Tüketim</h4>
                            <p className="text-info/80 text-xs">
                                Mevcut ortalama <b className="text-info">{stats?.current_consumption} L/100km</b> üzerinden,
                                AI desteği ile <b className="text-info">{stats?.target_consumption} L/100km</b> hedeflenmektedir.
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
                <div className="bg-surface p-8 rounded-[32px] border border-border shadow-sm flex items-center justify-between relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-r from-info/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="relative z-10">
                        <p className="text-xs font-black uppercase text-secondary mb-1">Aylık Potansiyel</p>
                        <h3 className="text-3xl font-black text-info">
                            {savings ? formatCurrency(savings.potential_savings / 12) : '-'}
                        </h3>
                    </div>
                    <div className="w-12 h-12 bg-info/10 rounded-2xl flex items-center justify-center text-info">
                        <TrendingUp className="w-6 h-6" />
                    </div>
                </div>

                <div className="bg-surface p-8 rounded-[32px] border border-border shadow-sm flex items-center justify-between relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-r from-success/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="relative z-10">
                        <p className="text-xs font-black uppercase text-secondary mb-1">Yıllık Tasarruf</p>
                        <h3 className="text-3xl font-black text-success">{stats ? formatCurrency(stats.annual_savings) : '-'}</h3>
                    </div>
                    <div className="w-12 h-12 bg-success/10 rounded-2xl flex items-center justify-center text-success">
                        <PiggyBank className="w-6 h-6" />
                    </div>
                </div>

                <div className="bg-surface p-8 rounded-[32px] border border-border shadow-sm flex items-center justify-between relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-r from-accent/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="relative z-10">
                        <p className="text-xs font-black uppercase text-secondary mb-1">ROI (Yatırım Getirisi)</p>
                        <h3 className="text-3xl font-black text-accent">%{stats ? stats.roi_percentage.toFixed(0) : '-'}</h3>
                    </div>
                    <div className="w-12 h-12 bg-accent/10 rounded-2xl flex items-center justify-center text-accent">
                        <TrendingUp className="w-6 h-6" />
                    </div>
                </div>

                {stats && stats.roi_percentage > 100 && (
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="p-4 bg-gradient-to-r from-accent to-accent/80 rounded-2xl text-accent-content text-center shadow-sm"
                    >
                        <p className="text-sm font-bold">🚀 Harika Yatırım! 12 aydan kısa sürede amorti ediyor.</p>
                    </motion.div>
                )}
            </motion.div>
        </div>
    )
}
