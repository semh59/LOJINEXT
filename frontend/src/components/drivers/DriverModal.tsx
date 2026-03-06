import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, User, Phone, Calendar, FileText } from 'lucide-react'
import { useForm, Controller, SubmitHandler } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Driver } from '../../types'

const driverSchema = z.object({
    ad_soyad: z.string()
        .min(3, 'İsim en az 3 karakter olmalı')
        .max(100, 'İsim en fazla 100 karakter olabilir'),
    telefon: z.string()
        .optional()
        .refine(val => !val || /^[0-9\s]{10,14}$/.test(val), 'Geçerli bir telefon numarası giriniz'),
    ise_baslama: z.string().optional(),
    ehliyet_sinifi: z.string().min(1, 'Ehliyet sınıfı seçiniz'),
    manual_score: z.number().min(0.1).max(2.0),
    notlar: z.string().max(500, 'Notlar en fazla 500 karakter olabilir').optional(),
    aktif: z.boolean()
})

type DriverFormData = z.infer<typeof driverSchema>

interface DriverModalProps {
    isOpen: boolean
    onClose: () => void
    onSave: (driver: Partial<Driver>) => Promise<void>
    driver?: Driver | null
}

const EHLIYET_OPTIONS = ['B', 'C', 'CE', 'D', 'D1E', 'E', 'G'] as const

export function DriverModal({ isOpen, onClose, onSave, driver }: DriverModalProps) {
    const {
        register,
        handleSubmit,
        control,
        reset,
        watch,
        formState: { errors, isSubmitting }
    } = useForm<DriverFormData>({
        resolver: zodResolver(driverSchema),
        defaultValues: {
            ad_soyad: '',
            telefon: '',
            ise_baslama: new Date().toISOString().split('T')[0],
            ehliyet_sinifi: 'E',
            manual_score: 1.0,
            notlar: '',
            aktif: true
        }
    })

    const notlar = watch('notlar') || ''
    const manualScore = watch('manual_score')

    useEffect(() => {
        if (isOpen) {
            if (driver) {
                reset({
                    ad_soyad: driver.ad_soyad || '',
                    telefon: driver.telefon || '',
                    ise_baslama: driver.ise_baslama?.split('T')[0] || '',
                    ehliyet_sinifi: driver.ehliyet_sinifi || 'E',
                    manual_score: driver.manual_score || 1.0,
                    notlar: driver.notlar || '',
                    aktif: driver.aktif ?? true
                })
            } else {
                reset({
                    ad_soyad: '',
                    telefon: '',
                    ise_baslama: new Date().toISOString().split('T')[0],
                    ehliyet_sinifi: 'E',
                    manual_score: 1.0,
                    notlar: '',
                    aktif: true
                })
            }
        }
    }, [driver, isOpen, reset])

    const onSubmit: SubmitHandler<DriverFormData> = async (data) => {
        try {
            const submitData = {
                ...data,
                telefon: data.telefon?.replace(/\s/g, ''),
            }
            await onSave(submitData)
            onClose()
        } catch (error) {
            console.error('Driver save error:', error)
        }
    }

    const formatPhone = (value: string): string => {
        const digits = value.replace(/\D/g, '').slice(0, 11)
        if (digits.length <= 4) return digits
        if (digits.length <= 7) return `${digits.slice(0, 4)} ${digits.slice(4)}`
        if (digits.length <= 9) return `${digits.slice(0, 4)} ${digits.slice(4, 7)} ${digits.slice(7)}`
        return `${digits.slice(0, 4)} ${digits.slice(4, 7)} ${digits.slice(7, 9)} ${digits.slice(9)}`
    }

    if (!isOpen) return null

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    className="bg-[#1a0121]/90 backdrop-blur-xl rounded-[32px] w-full max-w-lg border border-[#d006f9]/30 shadow-[0_0_40px_rgba(208,6,249,0.15)] overflow-hidden flex flex-col"
                >
                    <div className="flex items-center justify-between p-6 border-b border-[#d006f9]/20 bg-black/40 shrink-0">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-[#d006f9]/20 border border-[#d006f9]/40 rounded-xl flex items-center justify-center text-[#d006f9] shadow-[0_0_15px_rgba(208,6,249,0.3)]">
                                <User className="w-6 h-6" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-white">
                                    {driver ? 'Sürücüyü Düzenle' : 'Yeni Sürücü Ekle'}
                                </h2>
                                <p className="text-sm text-white/50">Sürücü bilgilerini giriniz</p>
                            </div>
                        </div>
                        <button onClick={onClose} className="p-2 text-white/50 hover:text-white hover:bg-white/10 rounded-xl transition-colors">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-white/50 uppercase tracking-wider flex items-center gap-2">
                                <User className="w-3.5 h-3.5" /> Ad Soyad *
                            </label>
                            <Input
                                {...register('ad_soyad')}
                                placeholder="Örn: Ahmet Yılmaz"
                                className="bg-black/40 border-[#d006f9]/30 text-white focus:border-[#d006f9]/60 shadow-[inset_0_2px_4px_rgba(0,0,0,0.3)]"
                                error={!!errors.ad_soyad}
                            />
                            {errors.ad_soyad && <p className="text-xs text-red-400 font-medium">{errors.ad_soyad.message}</p>}
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-white/50 uppercase tracking-wider flex items-center gap-2">
                                    <Phone className="w-3.5 h-3.5" /> Telefon
                                </label>
                                <Controller
                                    name="telefon"
                                    control={control}
                                    render={({ field }) => (
                                        <Input
                                            {...field}
                                            onChange={(e) => field.onChange(formatPhone(e.target.value))}
                                            placeholder="0532 123 45 67"
                                            className="bg-black/40 border-[#d006f9]/30 text-white focus:border-[#d006f9]/60"
                                            error={!!errors.telefon}
                                        />
                                    )}
                                />
                                {errors.telefon && <p className="text-xs text-red-400 font-medium">{errors.telefon.message}</p>}
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-white/50 uppercase tracking-wider">
                                    Ehliyet Sınıfı
                                </label>
                                <select
                                    {...register('ehliyet_sinifi')}
                                    className="w-full h-12 px-4 rounded-xl border border-[#d006f9]/30 bg-black/40 text-sm font-medium text-white focus:border-[#d006f9]/60 outline-none transition-all shadow-[inset_0_2px_4px_rgba(0,0,0,0.3)]"
                                >
                                    {EHLIYET_OPTIONS.map(cls => (
                                        <option key={cls} value={cls} className="bg-[#1a0121]">{cls} Sınıfı</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-white/50 uppercase tracking-wider flex items-center gap-2">
                                    <Calendar className="w-3.5 h-3.5" /> İşe Başlama
                                </label>
                                <Input type="date" {...register('ise_baslama')} className="bg-black/40 border-[#d006f9]/30 text-white focus:border-[#d006f9]/60" error={!!errors.ise_baslama} />
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-white/50 uppercase tracking-wider">
                                    Manuel Puan: <span className="text-[#d006f9]">{manualScore?.toFixed(1)}</span>
                                </label>
                                <input
                                    type="range"
                                    min="0.1"
                                    max="2.0"
                                    step="0.1"
                                    {...register('manual_score', { valueAsNumber: true })}
                                    className="w-full h-2 bg-black/50 rounded-lg appearance-none cursor-pointer accent-[#d006f9]"
                                />
                                <div className="flex justify-between text-[10px] text-white/30 font-medium">
                                    <span>0.1 Düşük</span>
                                    <span>2.0 Mükemmel</span>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-white/50 uppercase tracking-wider flex items-center gap-2">
                                <FileText className="w-3.5 h-3.5" />
                                Notlar <span className="text-white/30 font-normal">({notlar.length}/500)</span>
                            </label>
                            <textarea
                                {...register('notlar')}
                                placeholder="Sürücü hakkında notlar..."
                                rows={3}
                                className={`w-full px-4 py-3 rounded-xl border ${errors.notlar ? 'border-red-500' : 'border-[#d006f9]/30'} bg-black/40 text-sm text-white focus:border-[#d006f9]/60 outline-none transition-all resize-none shadow-[inset_0_2px_4px_rgba(0,0,0,0.3)]`}
                            />
                            {errors.notlar && <p className="text-xs text-red-400 font-medium">{errors.notlar.message}</p>}
                        </div>

                        <div className="pt-2">
                            <label className="flex items-center gap-3 cursor-pointer p-3 border border-white/10 rounded-xl hover:bg-black/30 transition-colors bg-black/20">
                                <input
                                    type="checkbox"
                                    {...register('aktif')}
                                    className="w-5 h-5 text-[#d006f9] rounded border-white/20 focus:ring-[#d006f9] bg-black/50"
                                />
                                <div>
                                    <span className="text-sm font-bold text-white">Sürücü Aktif</span>
                                    <p className="text-xs text-white/50">Pasif sürücüler seferlere atanamaz</p>
                                </div>
                            </label>
                        </div>

                        <div className="flex gap-4">
                            <Button type="button" variant="secondary" className="flex-1 h-12" onClick={onClose}>İptal</Button>
                            <Button 
                                type="submit" 
                                variant="glossy-purple"
                                className="flex-1 h-12" 
                                isLoading={isSubmitting}
                            >
                                {driver ? 'Güncelle' : 'Kaydet'}
                            </Button>
                        </div>
                    </form>
                </motion.div>
            </div>
        </AnimatePresence>
    )
}

