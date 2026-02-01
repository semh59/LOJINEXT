import { useEffect, useState } from 'react'
import { Modal } from '../ui/Modal'
import { Input } from '../ui/Input'
import { Button } from '../ui/Button'
import { FuelRecord } from '../../types'
import { vehiclesApi } from '../../services/api'

interface FuelModalProps {
    isOpen: boolean
    onClose: () => void
    onSave: (data: Partial<FuelRecord>) => Promise<void>
    record?: FuelRecord | null
}

export function FuelModal({ isOpen, onClose, onSave, record }: FuelModalProps) {
    const [loading, setLoading] = useState(false)
    const [vehicles, setVehicles] = useState<any[]>([])
    const [formData, setFormData] = useState<Partial<FuelRecord>>({
        tarih: new Date().toISOString().slice(0, 10),
        litre: 0,
        birim_fiyat: 0,
        toplam_tutar: 0,
        km_sayac: 0,
        depo_durumu: 'Doldu',
        durum: 'Bekliyor'
    })

    useEffect(() => {
        if (isOpen) {
            vehiclesApi.getAll({ limit: 100, aktif_only: true })
                .then(setVehicles)
                .catch(console.error)

            if (record) {
                setFormData({
                    ...record,
                    tarih: record.tarih.slice(0, 10) // Format YYYY-MM-DD
                })
            } else {
                setFormData({
                    tarih: new Date().toISOString().slice(0, 10),
                    litre: 0,
                    birim_fiyat: 0,
                    toplam_tutar: 0,
                    km_sayac: 0,
                    depo_durumu: 'Doldu',
                    durum: 'Bekliyor',
                    istasyon: ''
                })
            }
        }
    }, [isOpen, record])

    // Auto-calculate Total
    useEffect(() => {
        const total = (formData.litre || 0) * (formData.birim_fiyat || 0)
        if (Math.abs(total - (formData.toplam_tutar || 0)) > 0.1) {
            setFormData(prev => ({ ...prev, toplam_tutar: parseFloat(total.toFixed(2)) }))
        }
    }, [formData.litre, formData.birim_fiyat])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        try {
            await onSave(formData)
            onClose()
        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={record ? 'Yakıt Kaydını Düzenle' : 'Yeni Yakıt Kaydı'}
        >
            <p className="text-sm text-neutral-500 mb-6">Araç yakıt alım bilgilerini giriniz.</p>
            <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-neutral-500">Tarih</label>
                        <Input
                            type="date"
                            value={formData.tarih}
                            onChange={e => setFormData({ ...formData, tarih: e.target.value })}
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-neutral-500">Araç</label>
                        <select
                            value={formData.arac_id}
                            onChange={e => setFormData({ ...formData, arac_id: Number(e.target.value) })}
                            className="w-full h-10 px-3 rounded-lg border border-neutral-200 bg-white text-sm focus:ring-2 focus:ring-primary/20 outline-none"
                            required
                        >
                            <option value="">Seçiniz</option>
                            {vehicles.map(v => (
                                <option key={v.id} value={v.id}>{v.plaka} - {v.marka}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-xs font-bold text-neutral-500">İstasyon</label>
                    <Input
                        value={formData.istasyon || ''}
                        onChange={e => setFormData({ ...formData, istasyon: e.target.value })}
                        placeholder="Örn: Shell Maslak"
                        required
                    />
                </div>

                <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-neutral-500">Litre</label>
                        <Input
                            type="number" step="0.01"
                            value={formData.litre}
                            onChange={e => setFormData({ ...formData, litre: parseFloat(e.target.value) })}
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-neutral-500">Birim Fiyat (TL)</label>
                        <Input
                            type="number" step="0.01"
                            value={formData.birim_fiyat}
                            onChange={e => setFormData({ ...formData, birim_fiyat: parseFloat(e.target.value) })}
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-neutral-500">Toplam (Otomatik)</label>
                        <Input
                            type="number"
                            value={formData.toplam_tutar}
                            readOnly
                            className="bg-neutral-50 font-bold text-brand-dark"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-neutral-500">KM Sayaç</label>
                        <Input
                            type="number"
                            value={formData.km_sayac}
                            onChange={e => setFormData({ ...formData, km_sayac: Number(e.target.value) })}
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-neutral-500">Depo Durumu</label>
                        <select
                            value={formData.depo_durumu}
                            onChange={e => setFormData({ ...formData, depo_durumu: e.target.value as any })}
                            className="w-full h-10 px-3 rounded-lg border border-neutral-200 bg-white text-sm focus:ring-2 focus:ring-primary/20 outline-none"
                        >
                            <option value="Doldu">Tam Doldu</option>
                            <option value="Kısmi">Kısmi Alım</option>
                            <option value="Bilinmiyor">Bilinmiyor</option>
                        </select>
                    </div>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="secondary" onClick={onClose}>İptal</Button>
                    <Button type="submit" isLoading={loading}>Kaydet</Button>
                </div>
            </form>
        </Modal>
    )
}
