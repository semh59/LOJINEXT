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
const getScoreLabel = (score: number): { label: string; color: string; bg: string } => {
    if (score >= 1.8) return { label: 'Mükemmel', color: 'var(--success)', bg: 'rgba(var(--success-rgb), 0.1)' }
    if (score >= 1.5) return { label: 'İyi', color: 'rgba(var(--accent-rgb), 1)', bg: 'rgba(var(--accent-rgb), 0.1)' }
    if (score >= 1.2) return { label: 'Orta', color: 'var(--warning)', bg: 'rgba(var(--warning-rgb), 0.1)' }
    if (score >= 0.8) return { label: 'Düşük', color: 'var(--danger)', bg: 'rgba(var(--danger-rgb), 0.1)' }
    return { label: 'Çok Düşük', color: 'var(--danger)', bg: 'rgba(var(--danger-rgb), 0.1)' }
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
                    className="bg-surface rounded-[12px] shadow-xl border border-border w-full max-w-md overflow-hidden flex flex-col"
                >
                    {/* Header */}
                    <div className="bg-bg-elevated/30 border-b border-border p-6 text-primary relative shrink-0">
                        <button
                            onClick={onClose}
                            className="absolute top-4 right-4 p-2 text-secondary hover:text-primary hover:bg-bg-elevated rounded-full transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                        <div className="flex items-center gap-4">
                            <div className="w-14 h-14 bg-bg-elevated border border-border rounded-[10px] flex items-center justify-center shadow-sm">
                                <Star className="w-7 h-7 fill-accent/20 text-accent" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-primary tracking-tight">Puan Güncelle</h2>
                                <p className="text-secondary font-medium text-xs">{driver.ad_soyad}</p>
                            </div>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="p-6 space-y-6">
                        {/* Mevcut Durum */}
                        <div className="bg-bg-elevated/20 rounded-[10px] p-4 border border-border">
                            <p className="text-[10px] font-bold text-secondary uppercase tracking-widest mb-2">Mevcut Durum</p>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <span className="text-2xl font-bold text-primary">{(driver.score || 1.0).toFixed(2)}</span>
                                    <span 
                                        className="text-[10px] font-bold px-2 py-0.5 rounded-full border shrink-0"
                                        style={{ 
                                            backgroundColor: currentLabel.bg,
                                            color: currentLabel.color,
                                            borderColor: `${currentLabel.color}30`
                                        }}
                                    >
                                        {currentLabel.label}
                                    </span>
                                </div>
                                <div className="text-right text-[10px] text-secondary font-bold uppercase tracking-tight">
                                    <p>Manuel: {(driver.manual_score || 1.0).toFixed(1)}</p>
                                </div>
                            </div>
                        </div>

                        {/* Manuel Puan Slider */}
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <label className="text-xs font-bold text-secondary uppercase tracking-widest">Manuel Değerlendirme</label>
                                <span className="text-2xl font-bold text-accent">{score.toFixed(1)}</span>
                            </div>

                            <input
                                type="range"
                                min="0.1"
                                max="2.0"
                                step="0.1"
                                value={score}
                                onChange={e => setScore(parseFloat(e.target.value))}
                                className="w-full h-3 bg-bg-elevated rounded-lg appearance-none cursor-pointer accent-accent shadow-inner"
                                style={{
                                    background: `linear-gradient(to right, var(--danger), var(--warning), var(--success))`
                                }}
                            />

                            <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-wider">
                                <span className="bg-danger/10 border border-danger/20 px-3 py-1.5 rounded-lg text-danger">0.1 Riskli</span>
                                <span className="bg-warning/10 border border-warning/20 px-3 py-1.5 rounded-lg text-warning">1.0 Nötr</span>
                                <span className="bg-success/10 border border-success/20 px-3 py-1.5 rounded-lg text-success">2.0 Mükemmel</span>
                            </div>
                        </div>

                        {/* Tahmini Yeni Puan */}
                        <div className="bg-accent/5 rounded-[10px] p-4 border border-accent/10">
                            <div className="flex items-center gap-2 mb-3">
                                <TrendingUp className="w-4 h-4 text-accent" />
                                <p className="text-[10px] font-bold text-accent uppercase tracking-widest">Tahmini Hibrit Puan</p>
                            </div>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <span className="text-3xl font-bold text-primary">{estimatedHybrid.toFixed(2)}</span>
                                    <div className="flex items-center gap-0.5">
                                        {[1, 2, 3, 4, 5].map(i => (
                                            <Star
                                                key={i}
                                                className={`w-4 h-4 ${i <= stars ? 'fill-warning text-warning' : 'text-border'}`}
                                            />
                                        ))}
                                    </div>
                                </div>
                                <div className="text-right">
                                    <span
                                        className="text-[10px] font-bold px-2 py-0.5 rounded-full border shrink-0"
                                        style={{
                                            backgroundColor: newLabel.bg,
                                            color: newLabel.color,
                                            borderColor: `${newLabel.color}30`
                                        }}
                                    >
                                        {newLabel.label}
                                    </span>
                                    {scoreChange !== 0 && (
                                        <p className={`text-[10px] font-bold mt-1 uppercase tracking-tight ${scoreChange > 0 ? 'text-success' : 'text-danger'}`}>
                                            {scoreChange > 0 ? '+' : ''}{scoreChange.toFixed(2)}
                                        </p>
                                    )}
                                </div>
                            </div>
                            <p className="text-[9px] text-secondary/60 font-medium mt-2">
                                * Hibrit = %60 Performans + %40 Manuel Değerlendirme
                            </p>
                        </div>

                        {/* Actions */}
                        <div className="grid grid-cols-2 gap-3 pt-2">
                            <button
                                type="button"
                                onClick={onClose}
                                className="h-11 rounded-[8px] bg-bg-elevated border border-border text-primary hover:bg-bg-elevated/70 text-xs font-bold transition-colors"
                            >
                                İptal
                            </button>
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="h-11 rounded-[8px] bg-accent text-bg-base font-bold hover:bg-accent/90 transition-all flex items-center justify-center gap-2 disabled:opacity-50 text-xs shadow-sm shadow-accent/20"
                            >
                                {isLoading ? (
                                    <div className="w-4 h-4 border-2 border-bg-base/30 border-t-bg-base rounded-full animate-spin" />
                                ) : (
                                    <>
                                        <Save className="w-3.5 h-3.5" />
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
