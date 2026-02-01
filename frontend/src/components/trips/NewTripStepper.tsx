import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Trip, Vehicle, Driver } from '../../types'
import { vehiclesApi, driversApi } from '../../services/api'
import { Check, Truck, User, MapPin, ChevronRight, ChevronLeft } from 'lucide-react'

interface NewTripStepperProps {
    onComplete: (data: Partial<Trip>) => void
    onCancel: () => void
}

const steps = [
    { id: 1, title: 'Araç Seçimi', icon: Truck },
    { id: 2, title: 'Sürücü Ata', icon: User },
    { id: 3, title: 'Rota & Yük', icon: MapPin },
]

export function NewTripStepper({ onComplete, onCancel }: NewTripStepperProps) {
    const [currentStep, setCurrentStep] = useState(1)
    const [vehicles, setVehicles] = useState<Vehicle[]>([])
    const [drivers, setDrivers] = useState<Driver[]>([])

    const [formData, setFormData] = useState<Partial<Trip>>({
        durum: 'Planlandı',
        planlanan_cikis: new Date().toISOString().slice(0, 16)
    })

    useEffect(() => {
        vehiclesApi.getAll({ aktif_only: true }).then(setVehicles).catch(() => { })
        driversApi.getAll({ aktif_only: true }).then(setDrivers).catch(() => { })
    }, [])

    const handleNext = () => {
        if (currentStep < 3) setCurrentStep(c => c + 1)
        else onComplete(formData)
    }

    const handleBack = () => {
        if (currentStep > 1) setCurrentStep(c => c - 1)
        else onCancel()
    }

    return (
        <div className="glass p-8 rounded-[32px] border border-white/50 relative overflow-hidden">
            {/* Progress Bar */}
            <div className="flex justify-between relative mb-12">
                <div className="absolute top-1/2 left-0 right-0 h-1 bg-neutral-100 -z-10 rounded-full"></div>
                <div
                    className="absolute top-1/2 left-0 h-1 bg-indigo-500 -z-10 rounded-full transition-all duration-500"
                    style={{ width: `${((currentStep - 1) / 2) * 100}%` }}
                ></div>

                {steps.map((s) => {
                    const isActive = s.id === currentStep
                    const isCompleted = s.id < currentStep
                    const Icon = s.icon

                    return (
                        <div key={s.id} className="flex flex-col items-center gap-2 bg-white px-2">
                            <div
                                className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${isActive ? 'border-indigo-500 bg-indigo-600 text-white scale-110 shadow-lg shadow-indigo-500/30' :
                                    isCompleted ? 'border-emerald-500 bg-emerald-500 text-white' :
                                        'border-neutral-200 bg-white text-neutral-300'
                                    }`}
                            >
                                {isCompleted ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                            </div>
                            <span className={`text-xs font-bold ${isActive ? 'text-indigo-600' : 'text-neutral-400'}`}>
                                {s.title}
                            </span>
                        </div>
                    )
                })}
            </div>

            {/* Step Content */}
            <div className="min-h-[300px] max-h-[50vh] overflow-y-auto pr-2">
                <AnimatePresence mode="wait">
                    {currentStep === 1 && (
                        <motion.div
                            key="step1"
                            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                            className="space-y-4"
                        >
                            <h3 className="text-xl font-bold text-brand-dark mb-4 sticky top-0 bg-white/90 backdrop-blur-sm py-2 -mt-2">Hangi araç yola çıkacak?</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {vehicles.map(v => (
                                    <div
                                        key={v.id}
                                        onClick={() => setFormData({ ...formData, arac_id: v.id, arac_plaka: v.plaka })}
                                        className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${formData.arac_id === v.id
                                            ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-200'
                                            : 'border-neutral-100 hover:border-indigo-200 bg-white'
                                            }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-neutral-100 rounded-lg text-neutral-500">
                                                <Truck className="w-6 h-6" />
                                            </div>
                                            <div>
                                                <div className="font-bold text-neutral-900">{v.plaka}</div>
                                                <div className="text-xs text-neutral-500">{v.marka} - {v.model}</div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {currentStep === 2 && (
                        <motion.div
                            key="step2"
                            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                            className="space-y-4"
                        >
                            <h3 className="text-xl font-bold text-brand-dark mb-4 sticky top-0 bg-white/90 backdrop-blur-sm py-2 -mt-2">Sürücüyü belirleyin</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {drivers.map(d => (
                                    <div
                                        key={d.id}
                                        onClick={() => setFormData({ ...formData, sofor_id: d.id, sofor_ad_soyad: d.ad_soyad })}
                                        className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${formData.sofor_id === d.id
                                            ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-200'
                                            : 'border-neutral-100 hover:border-indigo-200 bg-white'
                                            }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-neutral-100 rounded-lg text-neutral-500">
                                                <User className="w-6 h-6" />
                                            </div>
                                            <div>
                                                <div className="font-bold text-neutral-900">{d.ad_soyad}</div>
                                                <div className="text-xs text-neutral-500">{d.ehliyet_sinifi} Sınıfı • Puan: {d.score}</div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {currentStep === 3 && (
                        <motion.div
                            key="step3"
                            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                            className="space-y-6"
                        >
                            <h3 className="text-xl font-bold text-brand-dark mb-4">Rota ve yük detayları</h3>
                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-neutral-500 ml-1">Çıkış Noktası</label>
                                    <Input
                                        value={formData.cikis_konum || ''}
                                        onChange={e => setFormData({ ...formData, cikis_konum: e.target.value })}
                                        placeholder="İstanbul Depo"
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-neutral-500 ml-1">Varış Noktası</label>
                                    <Input
                                        value={formData.varis_konum || ''}
                                        onChange={e => setFormData({ ...formData, varis_konum: e.target.value })}
                                        placeholder="Ankara Lojistik"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-neutral-500 ml-1">Yük Tipi</label>
                                    <Input
                                        value={formData.yuk_tipi || ''}
                                        onChange={e => setFormData({ ...formData, yuk_tipi: e.target.value })}
                                        placeholder="Gıda, Tekstil vb."
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-neutral-500 ml-1">Yük Miktarı (Ton)</label>
                                    <Input
                                        type="number"
                                        value={formData.yuk_miktari || ''}
                                        onChange={e => setFormData({ ...formData, yuk_miktari: Number(e.target.value) })}
                                        placeholder="15.5"
                                    />
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs font-bold text-neutral-500 ml-1">Planlanan Çıkış</label>
                                <Input
                                    type="datetime-local"
                                    value={formData.planlanan_cikis || ''}
                                    onChange={e => setFormData({ ...formData, planlanan_cikis: e.target.value })}
                                />
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Actions */}
            <div className="flex justify-between mt-8 pt-6 border-t border-neutral-100">
                <Button variant="secondary" onClick={handleBack}>
                    {currentStep === 1 ? 'İptal Et' : (
                        <><ChevronLeft className="w-4 h-4 mr-2" /> Geri</>
                    )}
                </Button>

                <Button
                    onClick={handleNext}
                    disabled={
                        (currentStep === 1 && !formData.arac_id) ||
                        (currentStep === 2 && !formData.sofor_id) ||
                        (currentStep === 3 && (!formData.cikis_konum || !formData.varis_konum))
                    }
                >
                    {currentStep === 3 ? 'Seferi Oluştur' : (
                        <>Devam Et <ChevronRight className="w-4 h-4 ml-2" /></>
                    )}
                </Button>
            </div>
        </div>
    )
}
