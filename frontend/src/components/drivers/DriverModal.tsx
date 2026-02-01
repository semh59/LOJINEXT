import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, User, Save, Phone, Calendar, FileText } from 'lucide-react'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Driver } from '../../types'

interface DriverModalProps {
    isOpen: boolean
    onClose: () => void
    onSave: (driver: Partial<Driver>) => Promise<void>
    driver?: Driver | null
}

// Ehliyet sınıfları
const EHLIYET_OPTIONS = ['B', 'C', 'CE', 'D', 'D1E', 'E', 'G'] as const

export function DriverModal({ isOpen, onClose, onSave, driver }: DriverModalProps) {
    const [formData, setFormData] = useState<Partial<Driver>>({
        ad_soyad: '',
        telefon: '',
        ise_baslama: '',
        ehliyet_sinifi: 'E',
        manual_score: 1.0,
        notlar: '',
        aktif: true
    })
    const [loading, setLoading] = useState(false)
    const [errors, setErrors] = useState<Record<string, string>>({})

    useEffect(() => {
        if (driver) {
            setFormData({
                ad_soyad: driver.ad_soyad || '',
                telefon: driver.telefon || '',
                ise_baslama: driver.ise_baslama?.split('T')[0] || '',
                ehliyet_sinifi: driver.ehliyet_sinifi || 'E',
                manual_score: driver.manual_score || 1.0,
                notlar: driver.notlar || '',
                aktif: driver.aktif ?? true
            })
        } else {
            setFormData({
                ad_soyad: '',
                telefon: '',
                ise_baslama: new Date().toISOString().split('T')[0],
                ehliyet_sinifi: 'E',
                manual_score: 1.0,
                notlar: '',
                aktif: true
            })
        }
        setErrors({})
    }, [driver, isOpen])

    // Form validation
    const validateForm = (): boolean => {
        const newErrors: Record<string, string> = {}

        if (!formData.ad_soyad || formData.ad_soyad.length < 3) {
            newErrors.ad_soyad = 'İsim en az 3 karakter olmalı'
        }
        if (formData.ad_soyad && formData.ad_soyad.length > 100) {
            newErrors.ad_soyad = 'İsim en fazla 100 karakter olabilir'
        }
        if (formData.telefon && !/^[0-9]{10,11}$/.test(formData.telefon.replace(/\s/g, ''))) {
            newErrors.telefon = 'Geçerli telefon formatı: 05XX XXX XXXX'
        }
        if (formData.notlar && formData.notlar.length > 500) {
            newErrors.notlar = 'Notlar en fazla 500 karakter olabilir'
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    // Telefon formatla
    const formatPhone = (value: string): string => {
        const digits = value.replace(/\D/g, '').slice(0, 11)
        if (digits.length <= 4) return digits
        if (digits.length <= 7) return `${digits.slice(0, 4)} ${digits.slice(4)}`
        if (digits.length <= 9) return `${digits.slice(0, 4)} ${digits.slice(4, 7)} ${digits.slice(7)}`
        return `${digits.slice(0, 4)} ${digits.slice(4, 7)} ${digits.slice(7, 9)} ${digits.slice(9)}`
    }

    const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const formatted = formatPhone(e.target.value)
        setFormData(prev => ({ ...prev, telefon: formatted }))
        if (errors.telefon) setErrors(prev => ({ ...prev, telefon: '' }))
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!validateForm()) return

        setLoading(true)
        try {
            // API'ye gönderilecek data
            const submitData = {
                ...formData,
                telefon: formData.telefon?.replace(/\s/g, ''), // Boşlukları kaldır
            }
            await onSave(submitData)
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
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    className="bg-white rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-neutral-100 bg-gradient-to-r from-primary/5 to-transparent">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary">
                                <User className="w-6 h-6" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-neutral-900">
                                    {driver ? 'Sürücüyü Düzenle' : 'Yeni Sürücü Ekle'}
                                </h2>
                                <p className="text-sm text-neutral-500">Sürücü bilgilerini giriniz</p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 rounded-xl transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="p-6 space-y-5">
                        {/* Ad Soyad */}
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-2">
                                <User className="w-3.5 h-3.5" />
                                Ad Soyad *
                            </label>
                            <Input
                                value={formData.ad_soyad}
                                onChange={e => {
                                    setFormData(prev => ({ ...prev, ad_soyad: e.target.value }))
                                    if (errors.ad_soyad) setErrors(prev => ({ ...prev, ad_soyad: '' }))
                                }}
                                placeholder="Örn: Ahmet Yılmaz"
                                className={errors.ad_soyad ? 'border-danger' : ''}
                            />
                            {errors.ad_soyad && (
                                <p className="text-xs text-danger font-medium">{errors.ad_soyad}</p>
                            )}
                        </div>

                        {/* Telefon & Ehliyet */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-2">
                                    <Phone className="w-3.5 h-3.5" />
                                    Telefon
                                </label>
                                <Input
                                    value={formData.telefon}
                                    onChange={handlePhoneChange}
                                    placeholder="0532 123 45 67"
                                    className={errors.telefon ? 'border-danger' : ''}
                                />
                                {errors.telefon && (
                                    <p className="text-xs text-danger font-medium">{errors.telefon}</p>
                                )}
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider">
                                    Ehliyet Sınıfı
                                </label>
                                <select
                                    className="w-full h-12 px-4 rounded-xl border border-neutral-200 bg-white text-sm font-medium focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                                    value={formData.ehliyet_sinifi}
                                    onChange={e => setFormData(prev => ({ ...prev, ehliyet_sinifi: e.target.value as any }))}
                                >
                                    {EHLIYET_OPTIONS.map(cls => (
                                        <option key={cls} value={cls}>{cls} Sınıfı</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* İşe Başlama & Manuel Puan */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-2">
                                    <Calendar className="w-3.5 h-3.5" />
                                    İşe Başlama
                                </label>
                                <Input
                                    type="date"
                                    value={formData.ise_baslama || ''}
                                    onChange={e => setFormData(prev => ({ ...prev, ise_baslama: e.target.value }))}
                                />
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider">
                                    Manuel Puan: <span className="text-primary">{formData.manual_score?.toFixed(1)}</span>
                                </label>
                                <input
                                    type="range"
                                    min="0.1"
                                    max="2.0"
                                    step="0.1"
                                    value={formData.manual_score || 1.0}
                                    onChange={e => setFormData(prev => ({ ...prev, manual_score: parseFloat(e.target.value) }))}
                                    className="w-full h-2 bg-neutral-100 rounded-lg appearance-none cursor-pointer accent-primary"
                                />
                                <div className="flex justify-between text-[10px] text-neutral-400 font-medium">
                                    <span>0.1 Düşük</span>
                                    <span>2.0 Mükemmel</span>
                                </div>
                            </div>
                        </div>

                        {/* Notlar */}
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-2">
                                <FileText className="w-3.5 h-3.5" />
                                Notlar <span className="text-neutral-400 font-normal">({formData.notlar?.length || 0}/500)</span>
                            </label>
                            <textarea
                                value={formData.notlar || ''}
                                onChange={e => {
                                    if (e.target.value.length <= 500) {
                                        setFormData(prev => ({ ...prev, notlar: e.target.value }))
                                    }
                                }}
                                placeholder="Sürücü hakkında notlar..."
                                rows={3}
                                className="w-full px-4 py-3 rounded-xl border border-neutral-200 bg-white text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none"
                            />
                            {errors.notlar && (
                                <p className="text-xs text-danger font-medium">{errors.notlar}</p>
                            )}
                        </div>

                        {/* Aktif Toggle */}
                        <div className="pt-2">
                            <label className="flex items-center gap-3 cursor-pointer p-3 border border-neutral-200 rounded-xl hover:bg-neutral-50 transition-colors">
                                <input
                                    type="checkbox"
                                    checked={formData.aktif}
                                    onChange={e => setFormData(prev => ({ ...prev, aktif: e.target.checked }))}
                                    className="w-5 h-5 text-primary rounded border-neutral-300 focus:ring-primary"
                                />
                                <div>
                                    <span className="text-sm font-bold text-neutral-700">Sürücü Aktif</span>
                                    <p className="text-xs text-neutral-400">Pasif sürücüler seferlere atanamaz</p>
                                </div>
                            </label>
                        </div>

                        {/* Actions */}
                        <div className="pt-4 flex gap-3">
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
                            >
                                <Save className="w-4 h-4 mr-2" />
                                {driver ? 'Güncelle' : 'Kaydet'}
                            </Button>
                        </div>
                    </form>
                </motion.div>
            </div>
        </AnimatePresence>
    )
}
