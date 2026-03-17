import { useEffect } from 'react'
import { useForm, SubmitHandler } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useQuery } from '@tanstack/react-query'
import { Modal } from '../ui/Modal'
import { Input } from '../ui/Input'
import { Button } from '../ui/Button'
import { FuelRecord } from '../../types'
import { vehicleService } from '../../services/api/vehicle-service'

const fuelSchema = z.object({
    tarih: z.string().min(1, 'Tarih zorunludur'),
    arac_id: z.number().min(1, 'Araç seçiniz'),
    istasyon: z.string().min(1, 'İstasyon zorunludur'),
    litre: z.number().min(0.1, 'Litre 0\'dan büyük olmalı'),
    fiyat_tl: z.number().min(0.1, 'Birim fiyat 0\'dan büyük olmalı'),
    toplam_tutar: z.number().min(0, 'Toplam tutar 0 veya daha fazla olmalı'),
    km_sayac: z.number().min(0, 'KM sayacı 0 veya daha fazla olmalı'),
    depo_durumu: z.enum(['Doldu', 'Kısmi']),
    durum: z.enum(['Bekliyor', 'Onaylandı', 'Reddedildi']),
    fis_no: z.string().optional()
})

type FuelFormData = z.infer<typeof fuelSchema>

interface FuelModalProps {
    isOpen: boolean
    onClose: () => void
    onSave: (data: Partial<FuelRecord>) => Promise<void>
    record?: FuelRecord | null
}

export function FuelModal({ isOpen, onClose, onSave, record }: FuelModalProps) {
    // Vehicles list with React Query
    const { data: vehiclesData = [] } = useQuery({
        queryKey: ['vehicles', { aktif_only: true }],
        queryFn: () => vehicleService.getAll({ limit: 100, aktif_only: true }),
        enabled: isOpen
    })
    const vehicles = (Array.isArray(vehiclesData) ? vehiclesData : (vehiclesData as any).items || []) as import('../../types').Vehicle[]

    const {
        register,
        handleSubmit,
        reset,
        watch,
        setValue,
        formState: { errors, isSubmitting }
    } = useForm<FuelFormData>({
        resolver: zodResolver(fuelSchema),
        defaultValues: {
            tarih: new Date().toISOString().slice(0, 10),
            litre: 0,
            fiyat_tl: 0,
            toplam_tutar: 0,
            km_sayac: 0,
            depo_durumu: 'Kısmi',
            durum: 'Bekliyor',
            istasyon: ''
        }
    })

    const watchLitre = watch('litre')
    const watchFiyatTl = watch('fiyat_tl')

    // Auto-calculate Total
    useEffect(() => {
        const total = (watchLitre || 0) * (watchFiyatTl || 0)
        setValue('toplam_tutar', parseFloat(total.toFixed(2)))
    }, [watchLitre, watchFiyatTl, setValue])

    useEffect(() => {
        if (isOpen) {
            if (record) {
                reset({
                    ...record,
                    tarih: record.tarih.slice(0, 10),
                    fiyat_tl: record.birim_fiyat || record.fiyat_tl || 0,
                    durum: record.durum || 'Bekliyor'
                } as any)
            } else {
                reset({
                    tarih: new Date().toISOString().slice(0, 10),
                    litre: 0,
                    fiyat_tl: 0,
                    toplam_tutar: 0,
                    km_sayac: 0,
                    depo_durumu: 'Kısmi',
                    durum: 'Bekliyor',
                    istasyon: ''
                })
            }
        }
    }, [isOpen, record, reset])

    const onSubmit: SubmitHandler<FuelFormData> = async (data) => {
        try {
            await onSave(data as any)
            onClose()
        } catch (error) {
            console.error('Fuel save error:', error)
        }
    }

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={record ? 'Yakıt Kaydını Düzenle' : 'Yeni Yakıt Kaydı'}
        >
            <p className="text-sm text-secondary mb-6">Araç yakıt alım bilgilerini giriniz.</p>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-secondary">Tarih</label>
                        <Input type="date" {...register('tarih')} error={!!errors.tarih} />
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-secondary">Araç</label>
                        <select
                            {...register('arac_id', { valueAsNumber: true })}
                            className={`w-full h-10 px-3 rounded-md border ${errors.arac_id ? 'border-danger focus:ring-danger/20' : 'border-border focus:ring-accent/20'} bg-bg-elevated text-primary text-sm focus:ring-2 outline-none transition-all`}
                        >
                            <option value="">Seçiniz</option>
                            {vehicles.map(v => (
                                <option key={v.id} value={v.id}>{v.plaka} — {v.marka}</option>
                            ))}
                        </select>
                        {errors.arac_id && <p className="text-xs text-danger font-medium mt-1">{errors.arac_id.message}</p>}
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-xs font-bold text-secondary">İstasyon</label>
                    <Input {...register('istasyon')} placeholder="Örn: Shell Maslak" error={!!errors.istasyon} />
                    {errors.istasyon && <p className="text-xs text-danger font-medium">{errors.istasyon.message}</p>}
                </div>

                <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-secondary">Litre</label>
                        <Input type="number" step="0.01" {...register('litre', { valueAsNumber: true })} error={!!errors.litre} />
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-secondary">Birim Fiyat (TL)</label>
                        <Input type="number" step="0.01" {...register('fiyat_tl', { valueAsNumber: true })} error={!!errors.fiyat_tl} />
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-secondary">Toplam (Otomatik)</label>
                        <Input
                            type="number"
                            {...register('toplam_tutar', { valueAsNumber: true })}
                            readOnly
                            className="bg-bg-elevated font-bold text-primary"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-secondary">KM Sayaç</label>
                        <Input type="number" {...register('km_sayac', { valueAsNumber: true })} error={!!errors.km_sayac} />
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-secondary">Fiş Numarası</label>
                        <Input {...register('fis_no')} placeholder="Örn: FIS-123" error={!!errors.fis_no} />
                    </div>
                </div>

                <div className="space-y-2">
                        <label className="text-xs font-bold text-secondary">Depo Durumu</label>
                    <select
                        {...register('depo_durumu')}
                        className="w-full h-10 px-3 rounded-md border border-border bg-bg-elevated text-primary text-sm focus:ring-2 focus:ring-accent/20 outline-none transition-all"
                    >
                        <option value="Doldu">Tam Doldu</option>
                        <option value="Kısmi">Kısmi Alım</option>
                        <option value="Bilinmiyor">Bilinmiyor</option>
                    </select>
                </div>

                <div className="flex gap-4 pt-4">
                    <Button type="button" variant="secondary" className="flex-1 h-10" onClick={onClose}>İptal</Button>
                    <Button type="submit" variant="primary" className="flex-1 h-10" isLoading={isSubmitting}>Kaydet</Button>
                </div>
            </form>
        </Modal>
    )
}
