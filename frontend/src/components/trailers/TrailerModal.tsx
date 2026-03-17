import { useState, useEffect } from 'react'
import { X, Save, Info } from 'lucide-react'
import { Dorse } from '../../types'
import { Button } from '../ui/Button'
import { motion, AnimatePresence } from 'framer-motion'

interface TrailerModalProps {
    isOpen: boolean
    onClose: () => void
    onSave: (data: Partial<Dorse>) => Promise<void>
    trailer: Dorse | null
}

export function TrailerModal({ isOpen, onClose, onSave, trailer }: TrailerModalProps) {
    const [formData, setFormData] = useState<Partial<Dorse>>({
        plaka: '',
        marka: '',
        tipi: 'Standart',
        yil: new Date().getFullYear(),
        bos_agirlik_kg: 6000,
        maks_yuk_kapasitesi_kg: 24000,
        lastik_sayisi: 6,
        dorse_lastik_direnc_katsayisi: 0.006,
        dorse_hava_direnci: 0.2,
        aktif: true,
        notlar: ''
    })

    const [loading, setLoading] = useState(false)

    useEffect(() => {
        if (trailer) {
            setFormData(trailer)
        } else {
            setFormData({
                plaka: '',
                marka: '',
                tipi: 'Standart',
                yil: new Date().getFullYear(),
                bos_agirlik_kg: 6000,
                maks_yuk_kapasitesi_kg: 24000,
                lastik_sayisi: 6,
                dorse_lastik_direnc_katsayisi: 0.006,
                dorse_hava_direnci: 0.2,
                aktif: true,
                notlar: ''
            })
        }
    }, [trailer, isOpen])

    if (!isOpen) return null

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        try {
            await onSave(formData)
            onClose()
        } catch (error) {
            console.error('Save error:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value, type } = e.target
        setFormData(prev => ({
            ...prev,
            [name]: type === 'number' ? (value === '' ? 0 : parseFloat(value)) : value
        }))
    }

    const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
        if (e.target.type === 'number') {
            e.target.select()
        }
    }



    const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, checked } = e.target
        setFormData(prev => ({
            ...prev,
            [name]: checked
        }))
    }

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={onClose}
                    className="absolute inset-0 bg-black/40 backdrop-blur-sm"
                />
                
                <motion.div 
                    initial={{ scale: 0.9, opacity: 0, y: 20 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.9, opacity: 0, y: 20 }}
                    className="relative w-full max-w-2xl bg-surface border border-accent/20 rounded-[32px] shadow-lg overflow-hidden"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-8 border-b border-border bg-gradient-to-r from-accent/5 to-transparent">
                        <div>
                            <h2 className="text-2xl font-bold text-primary tracking-tight">
                                {trailer ? 'Dorse Düzenle' : 'Yeni Dorse Ekle'}
                            </h2>
                            <p className="text-xs text-secondary font-medium uppercase tracking-widest mt-1">
                                {trailer ? `ID: ${trailer.id} | ${trailer.plaka}` : 'Lojistik Altyapı Entegrasyonu'}
                            </p>
                        </div>
                        <button 
                            onClick={onClose}
                            className="p-3 rounded-2xl bg-bg-elevated text-secondary hover:text-primary hover:bg-danger/10 transition-all"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="p-8 max-h-[70vh] overflow-y-auto custom-scrollbar">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {/* Temel Bilgiler */}
                            <div className="space-y-6">
                                <h3 className="text-accent text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                                    <div className="w-1.5 h-1.5 rounded-full bg-accent" />
                                    Temel Bilgiler
                                </h3>
                                
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-xs font-bold text-secondary uppercase tracking-wider mb-2">Plaka</label>
                                        <input
                                            type="text"
                                            name="plaka"
                                            value={formData.plaka}
                                            onChange={handleChange}
                                            required
                                            className="w-full bg-base border border-border rounded-xl px-4 py-3 text-primary focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/10 transition-all font-bold tracking-tight"
                                            placeholder="34 ABC 123"
                                        />
                                    </div>
                                    
                                    <div>
                                        <label className="block text-xs font-bold text-secondary uppercase tracking-wider mb-2">Marka</label>
                                        <input
                                            type="text"
                                            name="marka"
                                            value={formData.marka}
                                            onChange={handleChange}
                                            className="w-full bg-base border border-border rounded-xl px-4 py-3 text-primary focus:outline-none focus:border-accent transition-all"
                                            placeholder="Krone, Tırsan vb."
                                        />
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-xs font-bold text-secondary uppercase tracking-wider mb-2">Tip</label>
                                            <select
                                                name="tipi"
                                                value={formData.tipi}
                                                onChange={handleChange}
                                                className="w-full bg-base border border-border rounded-xl px-4 py-3 text-primary focus:outline-none focus:border-accent transition-all"
                                            >
                                                <option value="Standart">Standart</option>
                                                <option value="Frigo">Frigo</option>
                                                <option value="Tenteli">Tenteli</option>
                                                <option value="Damperli">Damperli</option>
                                                <option value="Lowbed">Lowbed</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-bold text-secondary uppercase tracking-wider mb-2">Model Yılı</label>
                                            <input
                                                type="number"
                                                name="yil"
                                                value={formData.yil}
                                                onChange={handleChange}
                                                className="w-full bg-base border border-border rounded-xl px-4 py-3 text-primary focus:outline-none focus:border-accent transition-all"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Teknik Parametreler */}
                            <div className="space-y-6">
                                <h3 className="text-accent text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                                    <div className="w-1.5 h-1.5 rounded-full bg-accent" />
                                    Fizik & Teknik Parametreler
                                </h3>

                                <div className="space-y-4 p-4 bg-bg-elevated rounded-2xl border border-border">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-[10px] font-bold text-secondary uppercase tracking-wider mb-2">Boş Ağırlık (kg)</label>
                                            <input
                                                type="number"
                                                name="bos_agirlik_kg"
                                                value={formData.bos_agirlik_kg}
                                                onChange={handleChange}
                                                onFocus={handleFocus}
                                                className="w-full bg-base border border-border rounded-xl px-3 py-2 text-primary text-sm focus:outline-none focus:border-accent transition-all"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-[10px] font-bold text-secondary uppercase tracking-wider mb-2">Yük Kapasitesi (kg)</label>
                                            <input
                                                type="number"
                                                name="maks_yuk_kapasitesi_kg"
                                                value={formData.maks_yuk_kapasitesi_kg}
                                                onChange={handleChange}
                                                onFocus={handleFocus}
                                                className="w-full bg-base border border-border rounded-xl px-3 py-2 text-primary text-sm focus:outline-none focus:border-accent transition-all"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-[10px] font-bold text-secondary uppercase tracking-wider mb-2">Lastik Sayısı</label>
                                        <input
                                            type="number"
                                            name="lastik_sayisi"
                                            value={formData.lastik_sayisi}
                                            onChange={handleChange}
                                            onFocus={handleFocus}
                                            className="w-full bg-base border border-border rounded-xl px-3 py-2 text-primary text-sm focus:outline-none focus:border-accent transition-all"
                                        />
                                    </div>

                                    <div className="pt-2">
                                        <div className="flex items-center gap-2 mb-2">
                                            <Info className="w-3 h-3 text-secondary" />
                                            <span className="text-[10px] font-medium text-secondary uppercase tracking-widest">Gelişmiş Katsayılar (Physics Engine)</span>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="block text-[9px] font-bold text-secondary/60 uppercase tracking-wider mb-1">Lastik Direnci (Crr)</label>
                                                <input
                                                    type="number"
                                                    step="0.001"
                                                    name="dorse_lastik_direnc_katsayisi"
                                                    value={formData.dorse_lastik_direnc_katsayisi}
                                                    onChange={handleChange}
                                                    onFocus={handleFocus}
                                                    className="w-full bg-base border border-border rounded-lg px-3 py-1.5 text-xs text-primary focus:outline-none border-dashed"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-[9px] font-bold text-secondary/40 uppercase tracking-wider mb-1">Hava Direnci Katkısı</label>
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    name="dorse_hava_direnci"
                                                    value={formData.dorse_hava_direnci}
                                                    onChange={handleChange}
                                                    onFocus={handleFocus}
                                                    className="w-full bg-base border border-border rounded-lg px-3 py-1.5 text-xs text-primary focus:outline-none border-dashed"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="mt-8 pt-8 border-t border-border grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div>
                                <label className="block text-xs font-bold text-secondary uppercase tracking-wider mb-2">Notlar</label>
                                <textarea
                                    name="notlar"
                                    value={formData.notlar}
                                    onChange={handleChange}
                                    rows={3}
                                    className="w-full bg-base border border-border rounded-xl px-4 py-3 text-primary focus:outline-none focus:border-accent transition-all resize-none text-sm"
                                    placeholder="Bakım geçmişi, lastik durumu vb."
                                />
                            </div>
                            <div className="flex items-end pb-4">
                                <label className="flex items-center gap-4 cursor-pointer p-4 bg-bg-elevated rounded-2xl border border-border hover:bg-accent/5 transition-all w-full">
                                    <div className="relative inline-flex items-center cursor-pointer">
                                        <input 
                                            type="checkbox" 
                                            name="aktif"
                                            checked={formData.aktif}
                                            onChange={handleCheckboxChange}
                                            className="sr-only peer" 
                                        />
                                        <div className="w-11 h-6 bg-secondary/20 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-bg-surface after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-base after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-sm font-bold text-primary uppercase tracking-tight">Aktif Kullanım Durumu</span>
                                        <span className="text-[10px] text-secondary">Pasifleştirilen dorseler seferlerde seçilemez.</span>
                                    </div>
                                </label>
                            </div>
                        </div>
                    </form>

                    {/* Footer */}
                    <div className="p-8 bg-surface/80 backdrop-blur-xl border-t border-border flex items-center justify-between">
                        <Button 
                            variant="ghost" 
                            onClick={onClose}
                            className="text-primary hover:bg-bg-elevated"
                        >
                            İptal
                        </Button>
                        <Button 
                            variant="primary" 
                            onClick={handleSubmit}
                            disabled={loading}
                            className="bg-accent hover:bg-accent-dark gap-2 px-10 shadow-lg"
                        >
                            {loading ? (
                                <div className="w-5 h-5 border-2 border-bg-base/30 border-t-bg-base rounded-full animate-spin" />
                            ) : (
                                <>
                                    <Save className="w-5 h-5" />
                                    {trailer ? 'Güncelle' : 'Kaydet'}
                                </>
                            )}
                        </Button>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    )
}
