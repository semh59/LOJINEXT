import { useState, useEffect } from 'react'
import { vehiclesApi, driversApi } from '../../services/api'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { PredictionRequest } from '../../types'
import { Brain, Gauge, ArrowRight, User, Mountain, TrendingDown } from 'lucide-react'

interface PredictionFormProps {
    onPredict: (data: PredictionRequest) => void
    isLoading: boolean
}

interface Vehicle {
    id: number
    plaka: string
    marka: string
}

interface Driver {
    id: number
    ad_soyad: string
    score: number
}

export function PredictionForm({ onPredict, isLoading }: PredictionFormProps) {
    const [vehicles, setVehicles] = useState<Vehicle[]>([])
    const [drivers, setDrivers] = useState<Driver[]>([])
    const [formData, setFormData] = useState<PredictionRequest>({
        arac_id: 0,
        mesafe_km: 0,
        ton: 0,
        ascent_m: 0,
        descent_m: 0,
        sofor_id: undefined,
        model_type: 'linear'
    })

    useEffect(() => {
        // Araçları yükle
        vehiclesApi.getAll({ limit: 100, aktif_only: true })
            .then(setVehicles)
            .catch(err => console.error('Araçlar yüklenemedi:', err))

        // Şoförleri yükle
        driversApi.getAll({ limit: 100, aktif_only: true })
            .then(setDrivers)
            .catch(err => console.error('Şoförler yüklenemedi:', err))
    }, [])

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        onPredict(formData)
    }

    const selectedDriver = drivers.find(d => d.id === formData.sofor_id)

    return (
        <form onSubmit={handleSubmit} className="glass p-8 rounded-[32px] border border-white/50 space-y-6">
            <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-indigo-100 rounded-xl text-indigo-600">
                    <Brain className="w-6 h-6" />
                </div>
                <div>
                    <h3 className="text-xl font-black text-brand-dark">Tahmin Parametreleri</h3>
                    <p className="text-sm text-neutral-500">Sefer detaylarını girerek yapay zeka tahmini alın.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Araç Seçimi */}
                <div className="space-y-2">
                    <label htmlFor="arac_id" className="text-xs font-bold text-neutral-500">Araç Seçimi *</label>
                    <select
                        id="arac_id"
                        value={formData.arac_id}
                        onChange={e => setFormData({ ...formData, arac_id: Number(e.target.value) })}
                        className="w-full h-12 px-4 rounded-xl border border-neutral-200 bg-white/50 text-sm font-medium focus:ring-2 focus:ring-primary/20 outline-none transition-all hover:bg-white"
                        required
                    >
                        <option value={0}>Araç Seçiniz</option>
                        {vehicles.map(v => (
                            <option key={v.id} value={v.id}>{v.plaka} - {v.marka}</option>
                        ))}
                    </select>
                </div>

                {/* Şoför Seçimi */}
                <div className="space-y-2">
                    <label htmlFor="sofor_id" className="text-xs font-bold text-neutral-500 flex items-center gap-2">
                        <User className="w-3 h-3" />
                        Şoför Seçimi
                    </label>
                    <select
                        id="sofor_id"
                        value={formData.sofor_id || ''}
                        onChange={e => setFormData({ ...formData, sofor_id: e.target.value ? Number(e.target.value) : undefined })}
                        className="w-full h-12 px-4 rounded-xl border border-neutral-200 bg-white/50 text-sm font-medium focus:ring-2 focus:ring-primary/20 outline-none transition-all hover:bg-white"
                    >
                        <option value="">Şoför Seçin (opsiyonel)</option>
                        {drivers.map(d => (
                            <option key={d.id} value={d.id}>{d.ad_soyad} (Puan: {d.score?.toFixed(1) || '1.0'})</option>
                        ))}
                    </select>
                    {selectedDriver && (
                        <p className="text-xs text-indigo-600">
                            Şoför puanı tahmine dahil edilecek: <strong>{selectedDriver.score?.toFixed(2) || '1.0'}</strong>
                        </p>
                    )}
                </div>

                {/* Mesafe */}
                <div className="space-y-2">
                    <label htmlFor="mesafe_km" className="text-xs font-bold text-neutral-500">Mesafe (KM) *</label>
                    <Input
                        id="mesafe_km"
                        type="number"
                        min="1"
                        max="10000"
                        value={formData.mesafe_km || ''}
                        onChange={e => setFormData({ ...formData, mesafe_km: Number(e.target.value) })}
                        className="h-12"
                        placeholder="Örn: 450"
                        required
                    />
                </div>

                {/* Yük Miktarı */}
                <div className="space-y-2">
                    <label htmlFor="ton" className="text-xs font-bold text-neutral-500">Yük Miktarı (Ton)</label>
                    <Input
                        id="ton"
                        type="number"
                        min="0"
                        max="50"
                        step="0.1"
                        value={formData.ton || ''}
                        onChange={e => setFormData({ ...formData, ton: Number(e.target.value) })}
                        className="h-12"
                        placeholder="Örn: 22.5"
                    />
                </div>

                {/* Tırmanış */}
                <div className="space-y-2">
                    <label htmlFor="ascent_m" className="text-xs font-bold text-neutral-500 flex items-center gap-2">
                        <Mountain className="w-3 h-3" />
                        Toplam Tırmanış (m)
                    </label>
                    <Input
                        id="ascent_m"
                        type="number"
                        min="0"
                        max="5000"
                        value={formData.ascent_m || ''}
                        onChange={e => setFormData({ ...formData, ascent_m: Number(e.target.value) })}
                        className="h-12"
                        placeholder="Örn: 500"
                    />
                </div>

                {/* İniş */}
                <div className="space-y-2">
                    <label htmlFor="descent_m" className="text-xs font-bold text-neutral-500 flex items-center gap-2">
                        <TrendingDown className="w-3 h-3" />
                        Toplam İniş (m)
                    </label>
                    <Input
                        id="descent_m"
                        type="number"
                        min="0"
                        max="5000"
                        value={formData.descent_m || ''}
                        onChange={e => setFormData({ ...formData, descent_m: Number(e.target.value) })}
                        className="h-12"
                        placeholder="Örn: 300"
                    />
                </div>
            </div>

            {/* Model Tipi */}
            <div className="space-y-2">
                <label className="text-xs font-bold text-neutral-500">Model Tipi</label>
                <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="radio"
                            name="model_type"
                            value="linear"
                            checked={formData.model_type === 'linear'}
                            onChange={() => setFormData({ ...formData, model_type: 'linear' })}
                            className="w-4 h-4 text-indigo-600"
                        />
                        <span className="text-sm font-medium">Linear (Hızlı)</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="radio"
                            name="model_type"
                            value="xgboost"
                            checked={formData.model_type === 'xgboost'}
                            onChange={() => setFormData({ ...formData, model_type: 'xgboost' })}
                            className="w-4 h-4 text-indigo-600"
                        />
                        <span className="text-sm font-medium">XGBoost (Daha Doğru)</span>
                    </label>
                </div>
            </div>

            <Button
                type="submit"
                className="w-full h-14 text-lg font-bold shadow-lg shadow-indigo-500/20 bg-indigo-600 hover:bg-indigo-700 mt-4"
                isLoading={isLoading}
                disabled={!formData.arac_id || !formData.mesafe_km}
            >
                <Gauge className="w-5 h-5 mr-2" />
                Tahmin Hesapla
                <ArrowRight className="w-5 h-5 ml-auto opacity-50" />
            </Button>
        </form>
    )
}
