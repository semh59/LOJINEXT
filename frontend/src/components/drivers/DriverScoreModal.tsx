import { useEffect, useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Driver } from '../../types'
import { X, Star, Save, TrendingUp } from 'lucide-react'

interface DriverScoreModalProps {
    isOpen: boolean
    onClose: () => void
    onSave: (score: number) => Promise<void>
    driver: Driver | null
}

// Hibrit puan hesaplama formülü (Plan: %60 performans + %40 manuel)
// Performans skorunu mevcut hibrit puandan tahmin et
const calculateHybridScore = (currentHybrid: number, newManual: number, oldManual: number): number => {
    // Mevcut hibrit = 0.6 * perf + 0.4 * old_manual
    // perf = (hibrit - 0.4 * old_manual) / 0.6
    const estimatedPerf = (currentHybrid - 0.4 * oldManual) / 0.6
    // Yeni hibrit = 0.6 * perf + 0.4 * new_manual
    const newHybrid = 0.6 * estimatedPerf + 0.4 * newManual
    return Math.max(0.1, Math.min(2.0, newHybrid))
}

// Score to Star mapping
const scoreToStars = (score: number): number => {
    if (score >= 1.8) return 5
    if (score >= 1.5) return 4
    if (score >= 1.2) return 3
    if (score >= 0.8) return 2
    return 1
}

// Skor seviyesi label
const getScoreLabel = (score: number): { label: string; color: string } => {
    if (score >= 1.8) return { label: 'Mükemmel', color: '#10B981' }
    if (score >= 1.5) return { label: 'İyi', color: '#3B82F6' }
    if (score >= 1.2) return { label: 'Orta', color: '#F59E0B' }
    if (score >= 0.8) return { label: 'Düşük', color: '#EF4444' }
    return { label: 'Çok Düşük', color: '#EF4444' }
}

export function DriverScoreModal({ isOpen, onClose, onSave, driver }: DriverScoreModalProps) {
    const [score, setScore] = useState(1.0)
    const [isLoading, setIsLoading] = useState(false)

    useEffect(() => {
        if (driver) {
            setScore(driver.manual_score || 1.0)
        }
    }, [driver, isOpen])

    // Tahmini hibrit puan hesapla
    const estimatedHybrid = useMemo(() => {
        if (!driver) return score
        return calculateHybridScore(
            driver.score || 1.0,
            score,
            driver.manual_score || 1.0
        )
    }, [driver, score])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!driver?.id) return

        setIsLoading(true)
        try {
            await onSave(score)
            onClose()
        } catch (error) {
            console.error('Score update failed', error)
        } finally {
            setIsLoading(false)
        }
    }

    if (!isOpen || !driver) return null

    const currentLabel = getScoreLabel(driver.score || 1.0)
    const newLabel = getScoreLabel(estimatedHybrid)
    const stars = scoreToStars(estimatedHybrid)
    const scoreChange = estimatedHybrid - (driver.score || 1.0)

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
                <motion.div
                    initial={{ opacity: 0, scale: 0.9, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9, y: 20 }}
                    className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
                >
                    {/* Header */}
                    <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-6 text-white relative">
                        <button
                            onClick={onClose}
                            className="absolute top-4 right-4 p-2 hover:bg-white/20 rounded-xl transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                        <div className="flex items-center gap-4">
                            <div className="w-14 h-14 bg-white/20 backdrop-blur-md rounded-2xl flex items-center justify-center">
                                <Star className="w-7 h-7 fill-white" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold">Puan Güncelle</h2>
                                <p className="text-white/80 font-medium">{driver.ad_soyad}</p>
                            </div>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="p-6 space-y-6">
                        {/* Mevcut Durum */}
                        <div className="bg-neutral-50 rounded-xl p-4 border border-neutral-100">
                            <p className="text-xs font-bold text-neutral-500 uppercase tracking-wider mb-2">Mevcut Durum</p>
                            <div className="flex items-center justify-between">
                                <div>
                                    <span className="text-2xl font-black text-neutral-800">{(driver.score || 1.0).toFixed(2)}</span>
                                    <span className="text-sm font-bold ml-2" style={{ color: currentLabel.color }}>
                                        {currentLabel.label}
                                    </span>
                                </div>
                                <div className="text-right text-xs text-neutral-400">
                                    <p>Manuel: {(driver.manual_score || 1.0).toFixed(1)}</p>
                                </div>
                            </div>
                        </div>

                        {/* Manuel Puan Slider */}
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <label className="text-sm font-bold text-neutral-700">Manuel Değerlendirme</label>
                                <span className="text-2xl font-black text-amber-500">{score.toFixed(1)}</span>
                            </div>

                            <input
                                type="range"
                                min="0.1"
                                max="2.0"
                                step="0.1"
                                value={score}
                                onChange={e => setScore(parseFloat(e.target.value))}
                                className="w-full h-3 bg-gradient-to-r from-red-200 via-yellow-200 to-green-200 rounded-lg appearance-none cursor-pointer"
                                style={{
                                    background: `linear-gradient(to right, #FEE2E2, #FEF3C7, #D1FAE5)`
                                }}
                            />

                            <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-wider">
                                <span className="bg-red-100 px-3 py-1.5 rounded-lg text-red-600">0.1 Riskli</span>
                                <span className="bg-yellow-100 px-3 py-1.5 rounded-lg text-yellow-700">1.0 Nötr</span>
                                <span className="bg-green-100 px-3 py-1.5 rounded-lg text-green-600">2.0 Mükemmel</span>
                            </div>
                        </div>

                        {/* Tahmini Yeni Puan */}
                        <div className="bg-gradient-to-r from-primary/5 to-brand/5 rounded-xl p-4 border border-primary/10">
                            <div className="flex items-center gap-2 mb-3">
                                <TrendingUp className="w-4 h-4 text-primary" />
                                <p className="text-xs font-bold text-primary uppercase tracking-wider">Tahmini Hibrit Puan</p>
                            </div>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <span className="text-3xl font-black text-neutral-800">{estimatedHybrid.toFixed(2)}</span>
                                    <div className="flex items-center gap-0.5">
                                        {[1, 2, 3, 4, 5].map(i => (
                                            <Star
                                                key={i}
                                                className={`w-4 h-4 ${i <= stars ? 'fill-amber-400 text-amber-400' : 'text-neutral-200'}`}
                                            />
                                        ))}
                                    </div>
                                </div>
                                <div className="text-right">
                                    <span
                                        className="text-sm font-bold px-2 py-1 rounded-lg"
                                        style={{
                                            backgroundColor: `${newLabel.color}15`,
                                            color: newLabel.color
                                        }}
                                    >
                                        {newLabel.label}
                                    </span>
                                    {scoreChange !== 0 && (
                                        <p className={`text-xs font-bold mt-1 ${scoreChange > 0 ? 'text-success' : 'text-danger'}`}>
                                            {scoreChange > 0 ? '+' : ''}{scoreChange.toFixed(2)}
                                        </p>
                                    )}
                                </div>
                            </div>
                            <p className="text-[10px] text-neutral-400 mt-2">
                                * Hibrit = %60 Performans + %40 Manuel Değerlendirme
                            </p>
                        </div>

                        {/* Actions */}
                        <div className="grid grid-cols-2 gap-3 pt-2">
                            <button
                                type="button"
                                onClick={onClose}
                                className="px-4 py-3 rounded-xl text-neutral-600 hover:bg-neutral-100 font-bold transition-colors border border-neutral-200"
                            >
                                İptal
                            </button>
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="px-4 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-white font-bold hover:shadow-lg hover:shadow-orange-500/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                {isLoading ? (
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                ) : (
                                    <>
                                        <Save className="w-4 h-4" />
                                        Güncelle
                                    </>
                                )}
                            </button>
                        </div>
                    </form>
                </motion.div>
            </div>
        </AnimatePresence>
    )
}
