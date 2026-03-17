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
            <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="bg-surface/90 backdrop-blur-xl rounded-[32px] border border-accent/20 shadow-2xl w-full max-w-2xl overflow-hidden relative flex flex-col"
                >
                    {/* Header */}
                    <div className="p-6 border-b border-border bg-bg-elevated/40 flex justify-between items-center shrink-0">
                        <div>
                            <h2 className="text-xl font-bold text-primary flex items-center gap-2">
                                <div className="w-10 h-10 bg-accent/20 border border-accent/40 rounded-xl flex items-center justify-center text-accent shadow-sm">
                                    <Award className="w-5 h-5" />
                                </div>
                                Sürücü Karnesi
                            </h2>
                            <p className="text-sm text-secondary mt-1">
                                {driver?.ad_soyad} • AI Performans Analizi
                            </p>
                        </div>
                        <button onClick={onClose} className="p-2 hover:bg-bg-elevated text-secondary hover:text-primary rounded-full transition-colors">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="p-8 min-h-[400px] overflow-y-auto custom-scrollbar">
                        {loading ? (
                            <div className="h-full flex flex-col items-center justify-center space-y-4 py-12">
                                <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin" />
                                <p className="text-secondary font-medium uppercase tracking-widest text-[10px]">Analiz ediliyor...</p>
                            </div>
                        ) : error ? (
                            <div className="h-full flex flex-col items-center justify-center text-danger space-y-2 py-12">
                                <AlertCircle className="w-10 h-10" />
                                <p>{error}</p>
                            </div>
                        ) : data ? (
                            <div className="space-y-8">
                                {/* Top Stats */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    {/* Total Score */}
                                    <div className="col-span-1 md:col-span-3 bg-gradient-to-r from-accent/10 to-success/10 border border-border rounded-[24px] p-6 text-primary text-center relative overflow-hidden shadow-sm">
                                        <div className="absolute top-0 right-0 w-32 h-32 bg-accent/20 rounded-full blur-[40px] -translate-y-1/2 translate-x-1/2" />
                                        <div className="absolute bottom-0 left-0 w-32 h-32 bg-success/10 rounded-full blur-[40px] translate-y-1/2 -translate-x-1/4" />
                                        <div className="relative z-10">
                                            <div className="text-sm font-bold text-secondary uppercase tracking-widest mb-1">Genel Performans Skoru</div>
                                            <div className="text-7xl font-black mb-3 text-primary drop-shadow-md">{data.total_score}</div>
                                            <div className="flex items-center justify-center gap-2 text-sm font-bold bg-surface/40 border border-border px-5 py-2 rounded-full w-max mx-auto shadow-inner">
                                                {data.trend === 'increasing' && <TrendingUp className="w-4 h-4 text-success" />}
                                                {data.trend === 'decreasing' && <TrendingDown className="w-4 h-4 text-danger" />}
                                                {data.trend === 'stable' && <Minus className="w-4 h-4 text-warning" />}
                                                <span className={cn(
                                                    data.trend === 'increasing' && 'text-success',
                                                    data.trend === 'decreasing' && 'text-danger',
                                                    data.trend === 'stable' && 'text-warning'
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
                                        color="text-success" 
                                        bg="bg-success/10 border-success/20" 
                                    />
                                    <ScoreCard 
                                        title="Ekonomik Sürüş" 
                                        score={data.eco_score} 
                                        icon={Leaf} 
                                        color="text-accent" 
                                        bg="bg-accent/10 border-accent/20" 
                                    />
                                    <ScoreCard 
                                        title="Kurallara Uyum" 
                                        score={data.compliance_score} 
                                        icon={Trophy} 
                                        color="text-warning" 
                                        bg="bg-warning/10 border-warning/20" 
                                    />
                                </div>

                                {/* Details Grid */}
                                <div className="grid grid-cols-2 gap-6 pt-6 border-t border-border">
                                    <div className="text-center p-6 bg-bg-elevated/40 border border-border rounded-[24px] shadow-inner">
                                        <div className="text-4xl font-black text-primary mb-2">{data.total_trips}</div>
                                        <div className="text-xs text-secondary uppercase font-bold tracking-wider">Analiz Edilen Sefer</div>
                                    </div>
                                    <div className="text-center p-6 bg-bg-elevated/40 border border-border rounded-[24px] shadow-inner">
                                        <div className="text-4xl font-black text-primary mb-2">{data.total_km}</div>
                                        <div className="text-xs text-secondary uppercase font-bold tracking-wider">Toplam KM</div>
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
        <div className={cn("p-6 rounded-[24px] border flex flex-col items-center justify-center text-center gap-3 transition-all hover:scale-[1.02] shadow-sm", bg)}>
            <div className={cn("p-4 rounded-xl shadow-lg border border-border bg-surface", color)}>
                <Icon className="w-8 h-8" />
            </div>
            <div className="font-bold text-secondary text-sm uppercase tracking-wider">{title}</div>
            <div className={cn("text-4xl font-black drop-shadow-sm", color)}>{score}</div>
        </div>
    )
}
