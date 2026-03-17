import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Truck, ChevronDown, ChevronUp, Settings2 } from 'lucide-react'
import { useForm, SubmitHandler } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Vehicle } from '../../types'

const vehicleSchema = z.object({
    plaka: z.string()
        .min(3, 'Plaka en az 3 karakter olmalı')
        .transform(val => val.replace(/\s+/g, '').toUpperCase()),
    marka: z.string().min(2, 'Marka en az 2 karakter olmalı').max(50),
    model: z.string().max(50).optional(),
    yil: z.number().min(1990).max(new Date().getFullYear() + 1),
    tank_kapasitesi: z.number().min(1).max(5000),
    hedef_tuketim: z.number().min(1).max(100),
    notlar: z.string().max(500).optional(),
    aktif: z.boolean(),
    // Fizik Parametreleri
    bos_agirlik_kg: z.number().min(0),
    hava_direnc_katsayisi: z.number().min(0),
    on_kesit_alani_m2: z.number().min(0),
    motor_verimliligi: z.number().min(0).max(1),
    lastik_direnc_katsayisi: z.number().min(0),
    maks_yuk_kapasitesi_kg: z.number().min(0)
})

type VehicleFormData = z.infer<typeof vehicleSchema>

interface VehicleModalProps {
    isOpen: boolean
    onClose: () => void
    onSave: (vehicle: Partial<Vehicle>) => Promise<void>
    vehicle?: Vehicle | null
}

const DEFAULT_PHYSICS = {
    bos_agirlik_kg: 8000,
    hava_direnc_katsayisi: 0.7,
    on_kesit_alani_m2: 8.5,
    motor_verimliligi: 0.38,
    lastik_direnc_katsayisi: 0.007,
    maks_yuk_kapasitesi_kg: 26000
}

export function VehicleModal({ isOpen, onClose, onSave, vehicle }: VehicleModalProps) {
    const [showAdvanced, setShowAdvanced] = useState(false)

    const {
        register,
        handleSubmit,
        reset,
        watch,
        formState: { errors, isSubmitting }
    } = useForm<VehicleFormData>({
        resolver: zodResolver(vehicleSchema),
        defaultValues: {
            plaka: '',
            marka: '',
            model: '',
            yil: new Date().getFullYear(),
            tank_kapasitesi: 600,
            hedef_tuketim: 32,
            notlar: '',
            aktif: true,
            ...DEFAULT_PHYSICS
        }
    })

    const notlar = watch('notlar') || ''

    useEffect(() => {
        if (isOpen) {
            if (vehicle) {
                reset({ ...DEFAULT_PHYSICS, ...vehicle } as any)
            } else {
                reset({
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
            setShowAdvanced(false)
        }
    }, [vehicle, isOpen, reset])

    const onSubmit: SubmitHandler<VehicleFormData> = async (data) => {
        try {
            await onSave(data)
            onClose()
        } catch (error) {
            console.error('Vehicle save error:', error)
        }
    }

    if (!isOpen) return null

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={onClose}
                    className="absolute inset-0 bg-black/40 backdrop-blur-sm"
                />
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    className="bg-surface rounded-[12px] w-full max-w-xl border border-border shadow-xl overflow-hidden max-h-[90vh] flex flex-col"
                >
                    <div className="flex items-center justify-between p-6 border-b border-border bg-bg-elevated shrink-0">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-bg-elevated border border-border rounded-[10px] flex items-center justify-center text-accent shadow-sm">
                                <Truck className="w-5 h-5" />
                            </div>
                            <div>
                                <h2 className="text-lg font-bold text-primary tracking-tight">
                                    {vehicle ? 'Aracı Düzenle' : 'Yeni Araç Ekle'}
                                </h2>
                                <p className="text-xs text-secondary font-medium">
                                    {vehicle ? 'Araç bilgilerini güncelleyin' : 'Filoya yeni araç ekleyin'}
                                </p>
                            </div>
                        </div>
                        <button onClick={onClose} className="p-2 text-secondary hover:text-primary hover:bg-surface rounded-full transition-colors">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col flex-1 overflow-hidden">
                        <div className="p-6 space-y-5 overflow-y-auto flex-1 custom-scrollbar bg-surface">
                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-secondary uppercase tracking-wider ml-1">Plaka *</label>
                                <Input
                                    {...register('plaka')}
                                    placeholder="34 ABC 123"
                                    className="font-mono uppercase text-lg tracking-wider"
                                    error={!!errors.plaka}
                                />
                                {errors.plaka && <p className="text-xs text-danger font-medium ml-1">{errors.plaka.message}</p>}
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-bold text-secondary uppercase tracking-wider ml-1">Marka *</label>
                                    <Input {...register('marka')} placeholder="Mercedes" error={!!errors.marka} />
                                    {errors.marka && <p className="text-xs text-danger font-medium ml-1">{errors.marka.message}</p>}
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-bold text-secondary uppercase tracking-wider ml-1">Model</label>
                                    <Input {...register('model')} placeholder="Actros" error={!!errors.model} />
                                    {errors.model && <p className="text-xs text-danger font-medium ml-1">{errors.model.message}</p>}
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-bold text-secondary uppercase tracking-wider ml-1">Yıl</label>
                                    <Input type="number" {...register('yil', { valueAsNumber: true })} error={!!errors.yil} />
                                    {errors.yil && <p className="text-xs text-danger font-medium ml-1">{errors.yil.message}</p>}
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-bold text-secondary uppercase tracking-wider ml-1">Tank Kapasitesi</label>
                                    <div className="relative">
                                        <Input type="number" {...register('tank_kapasitesi', { valueAsNumber: true })} className="pr-8" error={!!errors.tank_kapasitesi} />
                                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-secondary text-sm font-medium">L</span>
                                    </div>
                                    {errors.tank_kapasitesi && <p className="text-xs text-danger font-medium ml-1">{errors.tank_kapasitesi.message}</p>}
                                </div>
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-secondary uppercase tracking-wider ml-1">Hedef Tüketim</label>
                                <div className="relative max-w-[200px]">
                                    <Input type="number" step="0.1" {...register('hedef_tuketim', { valueAsNumber: true })} className="pr-20" error={!!errors.hedef_tuketim} />
                                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-secondary text-xs font-medium">L/100km</span>
                                </div>
                                {errors.hedef_tuketim && <p className="text-xs text-danger font-medium ml-1">{errors.hedef_tuketim.message}</p>}
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-xs font-bold text-secondary uppercase tracking-wider ml-1">Notlar</label>
                                <textarea
                                    {...register('notlar')}
                                    placeholder="Araç hakkında ek bilgiler..."
                                    rows={2}
                                    className="flex w-full rounded-md border border-border bg-bg-elevated text-primary px-3 py-2 text-sm focus-visible:outline-none focus-visible:border-accent resize-none transition-colors placeholder:text-secondary"
                                />
                                <p className="text-xs text-secondary text-right">{notlar.length}/500</p>
                            </div>

                            <label className="flex items-center gap-3 cursor-pointer p-3 border border-border rounded-xl hover:bg-bg-elevated transition-colors bg-surface">
                                <input type="checkbox" {...register('aktif')} className="w-5 h-5 text-accent rounded border-border focus:ring-accent bg-bg-elevated" />
                                <div>
                                    <span className="text-sm font-bold text-primary">Araç Aktif</span>
                                    <p className="text-xs text-secondary">Pasif araçlar listede gri görünür</p>
                                </div>
                            </label>

                            <div className="border border-border rounded-xl overflow-hidden bg-surface">
                                <button type="button" onClick={() => setShowAdvanced(!showAdvanced)} className="w-full flex items-center justify-between p-4 hover:bg-bg-elevated transition-colors">
                                    <div className="flex items-center gap-2">
                                        <Settings2 className="w-4 h-4 text-primary" />
                                        <span className="text-sm font-bold text-primary">Fizik Parametreleri</span>
                                    </div>
                                    {showAdvanced ? <ChevronUp className="w-4 h-4 text-secondary" /> : <ChevronDown className="w-4 h-4 text-secondary" />}
                                </button>
                                <AnimatePresence>
                                    {showAdvanced && (
                                        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="p-4 space-y-4 bg-bg-elevated border-t border-border">
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="space-y-1"><label className="text-xs font-medium text-secondary">Boş Ağırlık</label><Input type="number" {...register('bos_agirlik_kg', { valueAsNumber: true })} /></div>
                                                <div className="space-y-1"><label className="text-xs font-medium text-secondary">Hava Direnci (Cd)</label><Input type="number" step="0.01" {...register('hava_direnc_katsayisi', { valueAsNumber: true })} /></div>
                                                <div className="space-y-1"><label className="text-xs font-medium text-secondary">Ön Kesit</label><Input type="number" step="0.1" {...register('on_kesit_alani_m2', { valueAsNumber: true })} /></div>
                                                <div className="space-y-1"><label className="text-xs font-medium text-secondary">Motor Verimi</label><Input type="number" step="0.01" {...register('motor_verimliligi', { valueAsNumber: true })} /></div>
                                                <div className="space-y-1"><label className="text-xs font-medium text-secondary">Lastik Direnci</label><Input type="number" step="0.001" {...register('lastik_direnc_katsayisi', { valueAsNumber: true })} /></div>
                                                <div className="space-y-1"><label className="text-xs font-medium text-secondary">Max Yük Kapasitesi</label><Input type="number" {...register('maks_yuk_kapasitesi_kg', { valueAsNumber: true })} /></div>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>

                        <div className="p-6 border-t border-border bg-bg-elevated/30 shrink-0">
                            <div className="flex gap-4">
                                <Button type="button" variant="secondary" onClick={onClose} className="flex-1">İptal</Button>
                                <Button 
                                    type="submit" 
                                    variant="primary"
                                    className="flex-1 h-9" 
                                    isLoading={isSubmitting}
                                >
                                    {vehicle ? 'Güncelle' : 'Ekle'}
                                </Button>
                            </div>
                        </div>
                    </form>
                </motion.div>
            </div>
        </AnimatePresence>
    )
}
