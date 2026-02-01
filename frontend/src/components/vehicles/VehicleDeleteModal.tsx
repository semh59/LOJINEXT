import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, Trash2 } from 'lucide-react'
import { Button } from '../ui/Button'
import { Vehicle } from '../../types'

interface VehicleDeleteModalProps {
    isOpen: boolean
    onClose: () => void
    onConfirm: () => Promise<void>
    vehicle: Vehicle | null
}

export function VehicleDeleteModal({ isOpen, onClose, onConfirm, vehicle }: VehicleDeleteModalProps) {
    if (!isOpen || !vehicle) return null

    const isSoftDelete = vehicle.aktif

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    className="bg-white rounded-[32px] w-full max-w-md shadow-2xl overflow-hidden border border-neutral-100"
                >
                    <div className="p-8 text-center">
                        <div className={`w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-6 ${isSoftDelete ? 'bg-amber-50 text-amber-500' : 'bg-red-50 text-red-500'
                            }`}>
                            {isSoftDelete ? (
                                <AlertTriangle className="w-10 h-10" />
                            ) : (
                                <Trash2 className="w-10 h-10" />
                            )}
                        </div>

                        <h2 className="text-2xl font-black text-neutral-900 mb-2">
                            {isSoftDelete ? 'Aracı Pasife Al' : 'Kalıcı Olarak Sil'}
                        </h2>

                        <p className="text-neutral-500 font-medium mb-8 leading-relaxed">
                            <span className="font-bold text-neutral-800">{vehicle.plaka}</span> plakalı aracı
                            {isSoftDelete
                                ? ' pasif duruma getirmek üzeresiniz. Bu araç artık listelerde varsayılan olarak görünmeyecek ancak verileri saklanacaktır.'
                                : ' tamamen silmek üzeresiniz. Bu işlem geri alınamaz ve tüm geçmiş verileri kaybolacaktır.'}
                        </p>

                        <div className="flex gap-3">
                            <Button variant="secondary" onClick={onClose} className="flex-1 h-12 rounded-xl text-base">
                                İptal
                            </Button>
                            <Button
                                variant="danger"
                                onClick={async () => {
                                    await onConfirm()
                                    onClose()
                                }}
                                className={`flex-1 h-12 rounded-xl text-base ${isSoftDelete ? 'bg-amber-500 hover:bg-amber-600' : ''}`}
                            >
                                {isSoftDelete ? 'Pasife Al' : 'Evet, Sil'}
                            </Button>
                        </div>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    )
}
