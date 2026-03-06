import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Trophy, TrendingUp, TrendingDown, Minus, ShieldCheck, Leaf, AlertCircle, Award } from 'lucide-react'
import { driverService } from '../../services/api/driver-service'
import { Driver } from '../../types'
import { cn } from '../../lib/utils'

interface DriverPerformanceModalProps {
    isOpen: boolean
    onClose: () => void
    driver: Driver | null
}

interface PerformanceData {
    safety_score: number
    eco_score: number
    compliance_score: number
    total_score: number
    trend: 'increasing' | 'decreasing' | 'stable'
    total_km: number
    total_trips: number
}

export function DriverPerformanceModal({ isOpen, onClose, driver }: DriverPerformanceModalProps) {
    const [data, setData] = useState<PerformanceData | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (isOpen && driver?.id) {
            setLoading(true)
            setError(null)
            driverService.getPerformance(driver.id)
                .then(setData)
                .catch(err => {
                    console.error(err)
                    setError('Performans verileri alınamadı')
                })
                .finally(() => setLoading(false))
        } else {
            setData(null)
        }
    }, [isOpen, driver])

    if (!isOpen) return null

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="bg-[#1a0121]/90 backdrop-blur-xl rounded-[32px] border border-[#d006f9]/30 shadow-[0_0_40px_rgba(208,6,249,0.15)] w-full max-w-2xl overflow-hidden relative flex flex-col"
                >
                    {/* Header */}
                    <div className="p-6 border-b border-[#d006f9]/20 bg-black/40 flex justify-between items-center shrink-0">
                        <div>
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <div className="w-10 h-10 bg-[#d006f9]/20 border border-[#d006f9]/40 rounded-xl flex items-center justify-center text-[#d006f9] shadow-[0_0_15px_rgba(208,6,249,0.3)]">
                                    <Award className="w-5 h-5" />
                                </div>
                                Sürücü Karnesi
                            </h2>
                            <p className="text-sm text-white/50 mt-1">
                                {driver?.ad_soyad} • AI Performans Analizi
                            </p>
                        </div>
                        <button onClick={onClose} className="p-2 hover:bg-white/10 text-white/50 hover:text-white rounded-full transition-colors">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="p-8 min-h-[400px] overflow-y-auto custom-scrollbar">
                        {loading ? (
                            <div className="h-full flex flex-col items-center justify-center space-y-4 py-12">
                                <div className="w-12 h-12 border-4 border-[#d006f9] border-t-transparent rounded-full animate-spin" />
                                <p className="text-white/50 font-medium">Analiz ediliyor...</p>
                            </div>
                        ) : error ? (
                            <div className="h-full flex flex-col items-center justify-center text-red-400 space-y-2 py-12">
                                <AlertCircle className="w-10 h-10" />
                                <p>{error}</p>
                            </div>
                        ) : data ? (
                            <div className="space-y-8">
                                {/* Top Stats */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    {/* Total Score */}
                                    <div className="col-span-1 md:col-span-3 bg-gradient-to-r from-[#d006f9]/20 to-[#0df259]/20 border border-white/10 rounded-[24px] p-6 text-white text-center relative overflow-hidden shadow-[0_0_30px_rgba(208,6,249,0.1)]">
                                        <div className="absolute top-0 right-0 w-32 h-32 bg-[#d006f9]/30 rounded-full blur-[40px] -translate-y-1/2 translate-x-1/2" />
                                        <div className="absolute bottom-0 left-0 w-32 h-32 bg-[#0df259]/20 rounded-full blur-[40px] translate-y-1/2 -translate-x-1/4" />
                                        <div className="relative z-10">
                                            <div className="text-sm font-bold text-white/70 uppercase tracking-widest mb-1">Genel Performans Skoru</div>
                                            <div className="text-7xl font-black mb-3 text-transparent bg-clip-text bg-gradient-to-r from-white to-white/70 drop-shadow-md">{data.total_score}</div>
                                            <div className="flex items-center justify-center gap-2 text-sm font-bold bg-black/40 border border-white/10 px-5 py-2 rounded-full w-max mx-auto shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)]">
                                                {data.trend === 'increasing' && <TrendingUp className="w-4 h-4 text-[#0df259]" />}
                                                {data.trend === 'decreasing' && <TrendingDown className="w-4 h-4 text-red-400" />}
                                                {data.trend === 'stable' && <Minus className="w-4 h-4 text-amber-400" />}
                                                <span className={cn(
                                                    data.trend === 'increasing' && 'text-[#0df259]',
                                                    data.trend === 'decreasing' && 'text-red-400',
                                                    data.trend === 'stable' && 'text-amber-400'
                                                )}>
                                                    {data.trend === 'increasing' && 'Yükselişte'}
                                                    {data.trend === 'decreasing' && 'Düşüşte'}
                                                    {data.trend === 'stable' && 'Stabil'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Sub Scores */}
                                    <ScoreCard 
                                        title="Güvenli Sürüş" 
                                        score={data.safety_score} 
                                        icon={ShieldCheck} 
                                        color="text-[#0df259]" 
                                        bg="bg-[#0df259]/10 border-[#0df259]/20" 
                                    />
                                    <ScoreCard 
                                        title="Ekonomik Sürüş" 
                                        score={data.eco_score} 
                                        icon={Leaf} 
                                        color="text-blue-400" 
                                        bg="bg-blue-500/10 border-blue-500/20" 
                                    />
                                    <ScoreCard 
                                        title="Kurallara Uyum" 
                                        score={data.compliance_score} 
                                        icon={Trophy} 
                                        color="text-amber-400" 
                                        bg="bg-amber-500/10 border-amber-500/20" 
                                    />
                                </div>

                                {/* Details Grid */}
                                <div className="grid grid-cols-2 gap-6 pt-6 border-t border-white/10">
                                    <div className="text-center p-6 bg-black/40 border border-white/5 rounded-[24px] shadow-[inset_0_2px_10px_rgba(0,0,0,0.2)]">
                                        <div className="text-4xl font-black text-white mb-2">{data.total_trips}</div>
                                        <div className="text-xs text-white/50 uppercase font-bold tracking-wider">Analiz Edilen Sefer</div>
                                    </div>
                                    <div className="text-center p-6 bg-black/40 border border-white/5 rounded-[24px] shadow-[inset_0_2px_10px_rgba(0,0,0,0.2)]">
                                        <div className="text-4xl font-black text-white mb-2">{data.total_km}</div>
                                        <div className="text-xs text-white/50 uppercase font-bold tracking-wider">Toplam KM</div>
                                    </div>
                                </div>
                            </div>
                        ) : null}
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    )
}

function ScoreCard({ title, score, icon: Icon, color, bg }: any) {
    return (
        <div className={cn("p-6 rounded-[24px] border flex flex-col items-center justify-center text-center gap-3 transition-transform hover:-translate-y-1 hover:shadow-xl", bg)}>
            <div className={cn("p-4 rounded-xl shadow-lg border border-white/10 bg-black/40", color)}>
                <Icon className="w-8 h-8" />
            </div>
            <div className="font-bold text-white/60 text-sm uppercase tracking-wider">{title}</div>
            <div className={cn("text-4xl font-black drop-shadow-md", color)}>{score}</div>
        </div>
    )
}
