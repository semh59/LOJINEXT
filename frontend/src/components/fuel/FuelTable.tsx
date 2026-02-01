import { FuelRecord } from '../../types'
import { Edit2, Trash2, CheckCircle, Clock, XCircle } from 'lucide-react'
import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'

interface FuelTableProps {
    records: FuelRecord[]
    loading: boolean
    onEdit: (record: FuelRecord) => void
    onDelete: (record: FuelRecord) => void
}

export function FuelTable({ records, loading, onEdit, onDelete }: FuelTableProps) {
    const formatDate = (dateString: string) => {
        try {
            return new Intl.DateTimeFormat('tr-TR', { day: 'numeric', month: 'numeric' }).format(new Date(dateString))
        } catch { return dateString }
    }

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(amount)
    }

    if (loading) {
        return <div className="p-12 text-center text-neutral-400">Yükleniyor...</div>
    }

    if (records.length === 0) {
        return <div className="p-12 text-center text-neutral-400">Kayıt bulunamadı.</div>
    }

    return (
        <div className="w-full overflow-x-auto">
            <table className="w-full text-left border-collapse">
                <thead>
                    <tr className="border-b border-white/20 text-xs font-bold text-neutral-400 uppercase tracking-widest">
                        <th className="p-4">Tarih</th>
                        <th className="p-4">Araç</th>
                        <th className="p-4">İstasyon</th>
                        <th className="p-4">Litre</th>
                        <th className="p-4">Birim</th>
                        <th className="p-4">Toplam</th>
                        <th className="p-4">KM Sayaç</th>
                        <th className="p-4">Depo</th>
                        <th className="p-4">Durum</th>
                        <th className="p-4 text-right">İşlem</th>
                    </tr>
                </thead>
                <tbody className="text-sm font-medium text-neutral-700">
                    {records.map((record, i) => (
                        <motion.tr
                            key={record.id || i}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className="border-b border-white/10 hover:bg-white/40 group transition-colors"
                        >
                            <td className="p-4">{formatDate(record.tarih)}</td>
                            <td className="p-4 font-bold text-brand-dark">{record.plaka || `#${record.arac_id}`}</td>
                            <td className="p-4">{record.istasyon}</td>
                            <td className="p-4 text-blue-600 font-bold">{record.litre} L</td>
                            <td className="p-4 text-neutral-500">{formatCurrency(record.birim_fiyat)}/L</td>
                            <td className="p-4 font-black text-brand-dark">{formatCurrency(record.toplam_tutar)}</td>
                            <td className="p-4">{record.km_sayac.toLocaleString()} km</td>
                            <td className="p-4">
                                <span className={cn(
                                    "px-2 py-1 rounded-md text-[10px] uppercase font-black tracking-wide",
                                    record.depo_durumu === 'Doldu' ? "bg-emerald-100 text-emerald-700" :
                                        record.depo_durumu === 'Kısmi' ? "bg-amber-100 text-amber-700" :
                                            "bg-slate-100 text-slate-600"
                                )}>
                                    {record.depo_durumu}
                                </span>
                            </td>
                            <td className="p-4">
                                {record.durum === 'Onaylandı' && <CheckCircle className="w-4 h-4 text-emerald-500" />}
                                {record.durum === 'Bekliyor' && <Clock className="w-4 h-4 text-amber-500" />}
                                {record.durum === 'Reddedildi' && <XCircle className="w-4 h-4 text-red-500" />}
                                {!record.durum && <span className="text-neutral-300">-</span>}
                            </td>
                            <td className="p-4 text-right">
                                <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={() => onEdit(record)}
                                        className="p-2 hover:bg-blue-50 text-blue-600 rounded-lg transition-colors"
                                    >
                                        <Edit2 className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => onDelete(record)}
                                        className="p-2 hover:bg-red-50 text-red-600 rounded-lg transition-colors"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </td>
                        </motion.tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}
