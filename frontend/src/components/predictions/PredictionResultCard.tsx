import { PredictionResult } from '../../types'
import { motion } from 'framer-motion'
import { Droplets, TrendingDown, Cpu, Check } from 'lucide-react'

interface PredictionResultCardProps {
    result: PredictionResult | null
}

export function PredictionResultCard({ result }: PredictionResultCardProps) {
    if (!result) return (
        <div className="h-full min-h-[400px] bg-slate-100/50 rounded-[32px] border border-dashed border-slate-300 flex flex-col items-center justify-center text-center p-8">
            <div className="w-20 h-20 bg-slate-200 rounded-full flex items-center justify-center text-slate-400 mb-4">
                <Droplets className="w-10 h-10" />
            </div>
            <h3 className="text-lg font-bold text-slate-500">Henüz Tahmin Yapılmadı</h3>
            <p className="text-sm text-slate-400 max-w-xs mt-2">Sol taraftaki formu doldurarak yapay zeka destekli yakıt tüketim tahmini alabilirsiniz.</p>
        </div>
    )

    // Güven aralığı hesapla (backend sağlamazsa tahminden türet)
    const guvenAraligi = result.guven_araligi || {
        min: result.tahmini_tuketim * 0.9,
        max: result.tahmini_tuketim * 1.1
    }

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass p-8 rounded-[32px] border border-white/50 h-full relative overflow-hidden"
        >
            <div className="absolute top-0 right-0 p-8 opacity-10">
                <Droplets className="w-48 h-48 text-indigo-600" />
            </div>

            <div className="relative z-10">
                <p className="text-sm font-black uppercase text-indigo-400 tracking-wider mb-2">Tahmini Tüketim</p>
                <div className="flex items-baseline gap-2 mb-1">
                    <h2 className="text-6xl font-black text-brand-dark tracking-tighter">
                        {result.tahmini_tuketim.toFixed(1)}
                    </h2>
                    <span className="text-2xl font-bold text-neutral-400">L / 100km</span>
                </div>

                {/* Güven Aralığı */}
                <div className="flex items-center gap-2 text-sm font-bold text-neutral-500 mb-4 bg-white/50 w-fit px-3 py-1 rounded-full">
                    <span>Güven Aralığı:</span>
                    <span className="text-brand-dark">{guvenAraligi.min.toFixed(1)} - {guvenAraligi.max.toFixed(1)} L</span>
                </div>

                {/* Model Bilgisi */}
                <div className="flex items-center gap-2 text-sm font-medium text-neutral-600 mb-6 bg-indigo-50 w-fit px-3 py-1.5 rounded-full">
                    <Cpu className="w-4 h-4 text-indigo-500" />
                    <span>Model: <strong className="text-indigo-700">{result.model_used === 'xgboost' ? 'XGBoost Ensemble' : 'Linear Regression'}</strong></span>
                    {result.status === 'success' && <Check className="w-4 h-4 text-green-500" />}
                </div>

                {/* Tasarruf Önerisi (opsiyonel) */}
                {result.tasarruf_onerisi && (
                    <div className="bg-emerald-50 border border-emerald-100 p-4 rounded-2xl mb-6 flex items-start gap-3">
                        <TrendingDown className="w-5 h-5 text-emerald-600 mt-0.5" />
                        <div>
                            <h4 className="font-bold text-emerald-800 text-sm">Tasarruf Önerisi</h4>
                            <p className="text-emerald-700 text-xs mt-1 leading-relaxed">{result.tasarruf_onerisi}</p>
                        </div>
                    </div>
                )}

                {/* Faktörler (opsiyonel) */}
                {result.faktorler && result.faktorler.length > 0 && (
                    <div>
                        <h4 className="font-bold text-brand-dark mb-4 text-sm uppercase tracking-wide">Etkileyen Faktörler</h4>
                        <div className="space-y-3">
                            {result.faktorler.map((f, i) => (
                                <div key={i} className="flex justify-between items-center text-sm font-medium">
                                    <span className="text-neutral-600">{f.name}</span>
                                    <span className={`${f.impact > 0 ? 'text-red-500' : 'text-emerald-500'} font-bold bg-white px-2 py-0.5 rounded-lg shadow-sm border border-neutral-100`}>
                                        {f.impact > 0 ? '+' : ''}{f.impact}%
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Faktörler yoksa basit bilgi */}
                {(!result.faktorler || result.faktorler.length === 0) && (
                    <div className="mt-4 p-4 bg-neutral-50 rounded-xl border border-neutral-100">
                        <p className="text-sm text-neutral-600">
                            Bu tahmin <strong>{result.model_used === 'xgboost' ? 'XGBoost' : 'Linear'}</strong> modeli kullanılarak hesaplandı.
                            Araç özellikleri, yük miktarı ve güzergah parametreleri dikkate alındı.
                        </p>
                    </div>
                )}
            </div>
        </motion.div>
    )
}
