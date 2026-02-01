import { Driver } from '../../types'
import { motion } from 'framer-motion'
import { User, Phone, Star, Edit2, Trash2 } from 'lucide-react'

interface DriverCardProps {
    driver: Driver
    onEdit: (driver: Driver) => void
    onDelete: (id: number) => void
}

export function DriverCard({ driver, onEdit, onDelete }: DriverCardProps) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="group relative bg-white rounded-[24px] p-6 border border-neutral-200 hover:shadow-xl hover:shadow-indigo-500/10 transition-all duration-300"
        >
            <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                    onClick={() => onEdit(driver)}
                    className="p-2 bg-white/80 hover:bg-blue-50 text-neutral-400 hover:text-blue-600 rounded-full shadow-sm border border-neutral-100 transition-colors"
                >
                    <Edit2 className="w-4 h-4" />
                </button>
                <button
                    onClick={() => driver.id && onDelete(driver.id)}
                    className="p-2 bg-white/80 hover:bg-red-50 text-neutral-400 hover:text-red-600 rounded-full shadow-sm border border-neutral-100 transition-colors"
                >
                    <Trash2 className="w-4 h-4" />
                </button>
            </div>

            <div className="flex flex-col items-center text-center">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-50 to-blue-50 border-4 border-white shadow-lg flex items-center justify-center mb-4 relative">
                    <User className="w-8 h-8 text-indigo-400" />
                    {driver.aktif && (
                        <div className="absolute bottom-0 right-0 w-5 h-5 bg-emerald-500 border-2 border-white rounded-full" title="Aktif"></div>
                    )}
                </div>

                <h3 className="text-lg font-bold text-brand-dark mb-1">{driver.ad_soyad}</h3>

                <div className="flex items-center gap-1 mb-4">
                    <span className="px-2 py-0.5 bg-neutral-100 rounded text-xs font-bold text-neutral-500 border border-neutral-200">
                        {driver.ehliyet_sinifi} Sınıfı
                    </span>
                    <div className="flex items-center gap-1 px-2 py-0.5 bg-amber-50 rounded text-xs font-bold text-amber-700 border border-amber-100">
                        <Star className="w-3 h-3 fill-amber-500 text-amber-500" />
                        {driver.score}
                    </div>
                </div>

                <div className="w-full space-y-3">
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-neutral-50 border border-neutral-100">
                        <Phone className="w-4 h-4 text-neutral-400" />
                        <span className="text-sm font-medium text-neutral-600">{driver.telefon || '-'}</span>
                    </div>

                    {driver.ise_baslama && (
                        <div className="text-xs text-neutral-400 font-medium pt-2 border-t border-neutral-100">
                            İşe Başlama: {new Date(driver.ise_baslama).toLocaleDateString('tr-TR')}
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    )
}
