import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Truck, Save, ChevronDown, ChevronUp, Settings2, AlertCircle } from 'lucide-react'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Vehicle } from '../../types'

interface VehicleModalProps {
    isOpen: boolean
    onClose: () => void
    onSave: (vehicle: Partial<Vehicle>) => Promise<void>
    vehicle?: Vehicle | null
}

// Plakayı normalize et (boşlukları kaldır)
const normalizePlaka = (plaka: string): string => {
    return plaka.replace(/\s+/g, '').toUpperCase()
}

// Plaka geçerlilik kontrolü (sadece minimum uzunluk)
const validatePlaka = (plaka: string): boolean => {
    const normalized = normalizePlaka(plaka)
    // Boşsa kabul et (required kontrolü ayrı yapılacak)
    if (normalized.length === 0) return true
    // Minimum 3 karakter gerekli
    return normalized.length >= 3
}

// Default fizik parametreleri
const DEFAULT_PHYSICS = {
    bos_agirlik_kg: 8000,
    hava_direnc_katsayisi: 0.7,
    on_kesit_alani_m2: 8.5,
    motor_verimliligi: 0.38,
    lastik_direnc_katsayisi: 0.007,
    maks_yuk_kapasitesi_kg: 26000
}

export function VehicleModal({ isOpen, onClose, onSave, vehicle }: VehicleModalProps) {
    const [formData, setFormData] = useState<Partial<Vehicle>>({
        plaka: '',
        marka: '',
        model: '',
        yil: new Date().getFullYear(),
        tank_kapasitesi: 600,
        hedef_tuketim: 32,
        notlar: '',
        aktif: true,
        ...DEFAULT_PHYSICS
    })
    const [loading, setLoading] = useState(false)
    const [showAdvanced, setShowAdvanced] = useState(false)
    const [plakaError, setPlakaError] = useState<string | null>(null)

    useEffect(() => {
        if (vehicle) {
            setFormData({
                ...DEFAULT_PHYSICS,
                ...vehicle
            })
        } else {
            setFormData({
                plaka: '',
                marka: '',
                model: '',
                yil: new Date().getFullYear(),
                tank_kapasitesi: 600,
                hedef_tuketim: 32,
                notlar: '',
                aktif: true,
                ...DEFAULT_PHYSICS
            })
        }
        setPlakaError(null)
        setShowAdvanced(false)
    }, [vehicle, isOpen])

    // Plaka validasyonu (real-time)
    const handlePlakaChange = (value: string) => {
        const upper = value.toUpperCase()
        setFormData({ ...formData, plaka: upper })

        if (upper.length > 0 && !validatePlaka(upper)) {
            setPlakaError('Geçersiz plaka formatı (örn: 34ABC123)')
        } else {
            setPlakaError(null)
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        // Plaka validasyonu
        if (!formData.plaka || !validatePlaka(formData.plaka)) {
            setPlakaError('Lütfen geçerli bir plaka giriniz')
            return
        }

        setLoading(true)
        try {
            // Plakayı normalize et
            const normalizedData = {
                ...formData,
                plaka: normalizePlaka(formData.plaka!)
            }
            await onSave(normalizedData)
            onClose()
        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    if (!isOpen) return null

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    transition={{ duration: 0.2 }}
                    className="bg-white rounded-[32px] w-full max-w-xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-neutral-100 bg-neutral-50/50 shrink-0">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-500/25">
                                <Truck className="w-5 h-5" />
                            </div>
                            <div>
                                <h2 className="text-lg font-bold text-neutral-900">
                                    {vehicle ? 'Aracı Düzenle' : 'Yeni Araç Ekle'}
                                </h2>
                                <p className="text-xs text-neutral-500 font-medium">
                                    {vehicle ? 'Araç bilgilerini güncelleyin' : 'Filoya yeni araç ekleyin'}
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 text-neutral-400 hover:text-neutral-600 hover:bg-black/5 rounded-full transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="p-6 space-y-5 overflow-y-auto flex-1">
                        {/* Plaka - Full width */}
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider ml-1">
                                Plaka <span className="text-red-500">*</span>
                            </label>
                            <div className="relative">
                                <Input
                                    value={formData.plaka}
                                    onChange={e => handlePlakaChange(e.target.value)}
                                    placeholder="34 ABC 123"
                                    className={`font-mono uppercase text-lg tracking-wider ${plakaError ? 'border-red-500 focus-visible:ring-red-500' : ''}`}
                                    required
                                />
                                {plakaError && (
                                    <div className="flex items-center gap-1.5 mt-1.5 text-red-500 text-xs font-medium">
                                        <AlertCircle className="w-3.5 h-3.5" />
                                        {plakaError}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Marka + Model */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider ml-1">
                                    Marka <span className="text-red-500">*</span>
                                </label>
                                <Input
                                    value={formData.marka}
                                    onChange={e => setFormData({ ...formData, marka: e.target.value })}
                                    placeholder="Mercedes"
                                    required
                                    minLength={2}
                                    maxLength={50}
                                />
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider ml-1">
                                    Model
                                </label>
                                <Input
                                    value={formData.model}
                                    onChange={e => setFormData({ ...formData, model: e.target.value })}
                                    placeholder="Actros"
                                    maxLength={50}
                                />
                            </div>
                        </div>

                        {/* Yıl + Tank */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider ml-1">
                                    Yıl
                                </label>
                                <Input
                                    type="number"
                                    value={formData.yil}
                                    onChange={e => setFormData({ ...formData, yil: Number(e.target.value) })}
                                    min={1990}
                                    max={new Date().getFullYear() + 1}
                                />
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider ml-1">
                                    Tank Kapasitesi
                                </label>
                                <div className="relative">
                                    <Input
                                        type="number"
                                        value={formData.tank_kapasitesi}
                                        onChange={e => setFormData({ ...formData, tank_kapasitesi: Number(e.target.value) })}
                                        min={1}
                                        max={5000}
                                        className="pr-8"
                                    />
                                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 text-sm font-medium">
                                        L
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Hedef Tüketim */}
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider ml-1">
                                Hedef Tüketim
                            </label>
                            <div className="relative max-w-[200px]">
                                <Input
                                    type="number"
                                    step="0.1"
                                    value={formData.hedef_tuketim}
                                    onChange={e => setFormData({ ...formData, hedef_tuketim: Number(e.target.value) })}
                                    min={1}
                                    max={100}
                                    className="pr-20"
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 text-xs font-medium">
                                    L/100km
                                </span>
                            </div>
                        </div>

                        {/* Notlar */}
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider ml-1">
                                Notlar
                            </label>
                            <textarea
                                value={formData.notlar || ''}
                                onChange={e => setFormData({ ...formData, notlar: e.target.value })}
                                placeholder="Araç hakkında ek bilgiler..."
                                maxLength={500}
                                rows={2}
                                className="flex w-full rounded-xl border border-neutral-200 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-neutral-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 resize-none"
                            />
                            <p className="text-xs text-neutral-400 text-right">
                                {(formData.notlar?.length || 0)}/500
                            </p>
                        </div>

                        {/* Aktif Toggle */}
                        <label className="flex items-center gap-3 cursor-pointer p-3 border border-neutral-200 rounded-xl hover:bg-neutral-50 transition-colors">
                            <input
                                type="checkbox"
                                checked={formData.aktif}
                                onChange={e => setFormData({ ...formData, aktif: e.target.checked })}
                                className="w-5 h-5 text-primary rounded border-neutral-300 focus:ring-primary"
                            />
                            <div>
                                <span className="text-sm font-bold text-neutral-700">Araç Aktif</span>
                                <p className="text-xs text-neutral-500">Pasif araçlar listede gri görünür</p>
                            </div>
                        </label>

                        {/* Advanced - Fizik Parametreleri (Collapsible) */}
                        <div className="border border-neutral-200 rounded-xl overflow-hidden">
                            <button
                                type="button"
                                onClick={() => setShowAdvanced(!showAdvanced)}
                                className="w-full flex items-center justify-between p-4 bg-neutral-50 hover:bg-neutral-100 transition-colors"
                            >
                                <div className="flex items-center gap-2">
                                    <Settings2 className="w-4 h-4 text-neutral-500" />
                                    <span className="text-sm font-bold text-neutral-700">Fizik Parametreleri</span>
                                    <span className="text-xs text-neutral-400">(Gelişmiş)</span>
                                </div>
                                {showAdvanced ? (
                                    <ChevronUp className="w-4 h-4 text-neutral-500" />
                                ) : (
                                    <ChevronDown className="w-4 h-4 text-neutral-500" />
                                )}
                            </button>

                            <AnimatePresence>
                                {showAdvanced && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                        className="overflow-hidden"
                                    >
                                        <div className="p-4 space-y-4 bg-neutral-50/50">
                                            <div className="grid grid-cols-2 gap-4">
                                                {/* Boş Ağırlık */}
                                                <div className="space-y-1">
                                                    <label className="text-xs font-medium text-neutral-500">Boş Ağırlık</label>
                                                    <div className="relative">
                                                        <Input
                                                            type="number"
                                                            value={formData.bos_agirlik_kg}
                                                            onChange={e => setFormData({ ...formData, bos_agirlik_kg: Number(e.target.value) })}
                                                            className="pr-10 text-sm"
                                                        />
                                                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 text-xs">kg</span>
                                                    </div>
                                                </div>

                                                {/* Hava Direnci */}
                                                <div className="space-y-1">
                                                    <label className="text-xs font-medium text-neutral-500">Hava Direnci (Cd)</label>
                                                    <Input
                                                        type="number"
                                                        step="0.01"
                                                        value={formData.hava_direnc_katsayisi}
                                                        onChange={e => setFormData({ ...formData, hava_direnc_katsayisi: Number(e.target.value) })}
                                                        className="text-sm"
                                                    />
                                                </div>

                                                {/* Ön Kesit Alanı */}
                                                <div className="space-y-1">
                                                    <label className="text-xs font-medium text-neutral-500">Ön Kesit Alanı</label>
                                                    <div className="relative">
                                                        <Input
                                                            type="number"
                                                            step="0.1"
                                                            value={formData.on_kesit_alani_m2}
                                                            onChange={e => setFormData({ ...formData, on_kesit_alani_m2: Number(e.target.value) })}
                                                            className="pr-10 text-sm"
                                                        />
                                                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 text-xs">m²</span>
                                                    </div>
                                                </div>

                                                {/* Motor Verimi */}
                                                <div className="space-y-1">
                                                    <label className="text-xs font-medium text-neutral-500">Motor Verimi</label>
                                                    <Input
                                                        type="number"
                                                        step="0.01"
                                                        min="0"
                                                        max="1"
                                                        value={formData.motor_verimliligi}
                                                        onChange={e => setFormData({ ...formData, motor_verimliligi: Number(e.target.value) })}
                                                        className="text-sm"
                                                    />
                                                </div>

                                                {/* Lastik Direnci */}
                                                <div className="space-y-1">
                                                    <label className="text-xs font-medium text-neutral-500">Lastik Direnci</label>
                                                    <Input
                                                        type="number"
                                                        step="0.001"
                                                        value={formData.lastik_direnc_katsayisi}
                                                        onChange={e => setFormData({ ...formData, lastik_direnc_katsayisi: Number(e.target.value) })}
                                                        className="text-sm"
                                                    />
                                                </div>

                                                {/* Max Yük */}
                                                <div className="space-y-1">
                                                    <label className="text-xs font-medium text-neutral-500">Max Yük Kapasitesi</label>
                                                    <div className="relative">
                                                        <Input
                                                            type="number"
                                                            value={formData.maks_yuk_kapasitesi_kg}
                                                            onChange={e => setFormData({ ...formData, maks_yuk_kapasitesi_kg: Number(e.target.value) })}
                                                            className="pr-10 text-sm"
                                                        />
                                                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 text-xs">kg</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </form>

                    {/* Footer */}
                    <div className="p-6 border-t border-neutral-100 bg-neutral-50/50 flex gap-3 shrink-0">
                        <Button
                            type="button"
                            variant="secondary"
                            className="flex-1"
                            onClick={onClose}
                        >
                            İptal
                        </Button>
                        <Button
                            type="submit"
                            className="flex-1"
                            isLoading={loading}
                            onClick={handleSubmit}
                        >
                            <Save className="w-4 h-4 mr-2" />
                            Kaydet
                        </Button>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    )
}
