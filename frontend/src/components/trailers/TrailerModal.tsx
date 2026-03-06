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
                    className="absolute inset-0 bg-black/80 backdrop-blur-md"
                />
                
                <motion.div 
                    initial={{ scale: 0.9, opacity: 0, y: 20 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.9, opacity: 0, y: 20 }}
                    className="relative w-full max-w-2xl bg-[#1a0121] border border-[#d006f9]/30 rounded-[32px] shadow-[0_0_50px_rgba(208,6,249,0.2)] overflow-hidden"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-8 border-b border-[#d006f9]/10 bg-gradient-to-r from-[#d006f9]/5 to-transparent">
                        <div>
                            <h2 className="text-2xl font-bold text-white tracking-tight">
                                {trailer ? 'Dorse Düzenle' : 'Yeni Dorse Ekle'}
                            </h2>
                            <p className="text-xs text-[#d006f9]/60 font-medium uppercase tracking-widest mt-1">
                                {trailer ? `ID: ${trailer.id} | ${trailer.plaka}` : 'Lojistik Altyapı Entegrasyonu'}
                            </p>
                        </div>
                        <button 
                            onClick={onClose}
                            className="p-3 rounded-2xl bg-white/5 text-[#d006f9]/60 hover:text-white hover:bg-red-500/20 transition-all"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="p-8 max-h-[70vh] overflow-y-auto custom-scrollbar">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {/* Temel Bilgiler */}
                            <div className="space-y-6">
                                <h3 className="text-[#d006f9] text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                                    <div className="w-1.5 h-1.5 rounded-full bg-[#d006f9]" />
                                    Temel Bilgiler
                                </h3>
                                
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-xs font-bold text-[#d006f9]/60 uppercase tracking-wider mb-2">Plaka</label>
                                        <input
                                            type="text"
                                            name="plaka"
                                            value={formData.plaka}
                                            onChange={handleChange}
                                            required
                                            className="w-full bg-black/40 border border-[#d006f9]/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#d006f9] focus:shadow-[0_0_15px_rgba(208,6,249,0.2)] transition-all font-bold tracking-tight"
                                            placeholder="34 ABC 123"
                                        />
                                    </div>
                                    
                                    <div>
                                        <label className="block text-xs font-bold text-[#d006f9]/60 uppercase tracking-wider mb-2">Marka</label>
                                        <input
                                            type="text"
                                            name="marka"
                                            value={formData.marka}
                                            onChange={handleChange}
                                            className="w-full bg-black/40 border border-[#d006f9]/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#d006f9] transition-all"
                                            placeholder="Krone, Tırsan vb."
                                        />
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-xs font-bold text-[#d006f9]/60 uppercase tracking-wider mb-2">Tip</label>
                                            <select
                                                name="tipi"
                                                value={formData.tipi}
                                                onChange={handleChange}
                                                className="w-full bg-black/40 border border-[#d006f9]/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#d006f9] transition-all"
                                            >
                                                <option value="Standart">Standart</option>
                                                <option value="Frigo">Frigo</option>
                                                <option value="Tenteli">Tenteli</option>
                                                <option value="Damperli">Damperli</option>
                                                <option value="Lowbed">Lowbed</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-bold text-[#d006f9]/60 uppercase tracking-wider mb-2">Model Yılı</label>
                                            <input
                                                type="number"
                                                name="yil"
                                                value={formData.yil}
                                                onChange={handleChange}
                                                className="w-full bg-black/40 border border-[#d006f9]/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#d006f9] transition-all"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Teknik Parametreler */}
                            <div className="space-y-6">
                                <h3 className="text-[#d006f9] text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                                    <div className="w-1.5 h-1.5 rounded-full bg-[#d006f9]" />
                                    Fizik & Teknik Parametreler
                                </h3>

                                <div className="space-y-4 p-4 bg-black/20 rounded-2xl border border-[#d006f9]/5">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-[10px] font-bold text-[#d006f9]/40 uppercase tracking-wider mb-2">Boş Ağırlık (kg)</label>
                                            <input
                                                type="number"
                                                name="bos_agirlik_kg"
                                                value={formData.bos_agirlik_kg}
                                                onChange={handleChange}
                                                onFocus={handleFocus}
                                                className="w-full bg-black/40 border border-[#d006f9]/20 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-[#d006f9] transition-all"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-[10px] font-bold text-[#d006f9]/40 uppercase tracking-wider mb-2">Yük Kapasitesi (kg)</label>
                                            <input
                                                type="number"
                                                name="maks_yuk_kapasitesi_kg"
                                                value={formData.maks_yuk_kapasitesi_kg}
                                                onChange={handleChange}
                                                onFocus={handleFocus}
                                                className="w-full bg-black/40 border border-[#d006f9]/20 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-[#d006f9] transition-all"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-[10px] font-bold text-[#d006f9]/40 uppercase tracking-wider mb-2">Lastik Sayısı</label>
                                        <input
                                            type="number"
                                            name="lastik_sayisi"
                                            value={formData.lastik_sayisi}
                                            onChange={handleChange}
                                            onFocus={handleFocus}
                                            className="w-full bg-black/40 border border-[#d006f9]/20 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-[#d006f9] transition-all"
                                        />
                                    </div>

                                    <div className="pt-2">
                                        <div className="flex items-center gap-2 mb-2">
                                            <Info className="w-3 h-3 text-[#d006f9]/60" />
                                            <span className="text-[10px] font-medium text-[#d006f9]/60 uppercase tracking-widest">Gelişmiş Katsayılar (Physics Engine)</span>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="block text-[9px] font-bold text-[#d006f9]/30 uppercase tracking-wider mb-1">Lastik Direnci (Crr)</label>
                                                <input
                                                    type="number"
                                                    step="0.001"
                                                    name="dorse_lastik_direnc_katsayisi"
                                                    value={formData.dorse_lastik_direnc_katsayisi}
                                                    onChange={handleChange}
                                                    onFocus={handleFocus}
                                                    className="w-full bg-black/40 border border-[#d006f9]/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none border-dashed"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-[9px] font-bold text-[#d006f9]/30 uppercase tracking-wider mb-1">Hava Direnci Katkısı</label>
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    name="dorse_hava_direnci"
                                                    value={formData.dorse_hava_direnci}
                                                    onChange={handleChange}
                                                    onFocus={handleFocus}
                                                    className="w-full bg-black/40 border border-[#d006f9]/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none border-dashed"
                                                />

                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="mt-8 pt-8 border-t border-[#d006f9]/10 grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div>
                                <label className="block text-xs font-bold text-[#d006f9]/60 uppercase tracking-wider mb-2">Notlar</label>
                                <textarea
                                    name="notlar"
                                    value={formData.notlar}
                                    onChange={handleChange}
                                    rows={3}
                                    className="w-full bg-black/40 border border-[#d006f9]/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#d006f9] transition-all resize-none text-sm"
                                    placeholder="Bakım geçmişi, lastik durumu vb."
                                />
                            </div>
                            <div className="flex items-end pb-4">
                                <label className="flex items-center gap-4 cursor-pointer p-4 bg-white/5 rounded-2xl border border-[#d006f9]/10 hover:bg-[#d006f9]/5 transition-all w-full">
                                    <div className="relative inline-flex items-center cursor-pointer">
                                        <input 
                                            type="checkbox" 
                                            name="aktif"
                                            checked={formData.aktif}
                                            onChange={handleCheckboxChange}
                                            className="sr-only peer" 
                                        />
                                        <div className="w-11 h-6 bg-neutral-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#d006f9]"></div>
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-sm font-bold text-white uppercase tracking-tight">Aktif Kullanım Durumu</span>
                                        <span className="text-[10px] text-[#d006f9]/60">Pasifleştirilen dorseler seferlerde seçilemez.</span>
                                    </div>
                                </label>
                            </div>
                        </div>
                    </form>

                    {/* Footer */}
                    <div className="p-8 bg-black/40 backdrop-blur-xl border-t border-[#d006f9]/10 flex items-center justify-between">
                        <Button 
                            variant="ghost" 
                            onClick={onClose}
                            className="text-white hover:bg-white/10"
                        >
                            İptal
                        </Button>
                        <Button 
                            variant="primary" 
                            onClick={handleSubmit}
                            disabled={loading}
                            className="bg-[#d006f9] hover:bg-[#b005d4] gap-2 px-10 shadow-[0_0_20px_rgba(208,6,249,0.3)]"
                        >
                            {loading ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
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
