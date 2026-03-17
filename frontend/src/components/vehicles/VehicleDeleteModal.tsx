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
            <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-bg-base/20 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    className="bg-surface rounded-2xl w-full max-w-md shadow-2xl overflow-hidden border border-border"
                >
                    <div className="p-8 text-center">
                        <div className={`w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 ${isSoftDelete ? 'bg-warning/10 text-warning' : 'bg-danger/10 text-danger'
                            }`}>
                            {isSoftDelete ? (
                                <AlertTriangle className="w-10 h-10" />
                            ) : (
                                <Trash2 className="w-10 h-10" />
                            )}
                        </div>

                        <h2 className="text-2xl font-black text-primary mb-2">
                            {isSoftDelete ? 'Aracı Pasife Al' : 'Kalıcı Olarak Sil'}
                        </h2>

                        <p className="text-secondary font-medium mb-8 leading-relaxed">
                            <span className="font-bold text-primary">{vehicle.plaka}</span> plakalı aracı
                            {isSoftDelete
                                ? ' pasif duruma getirmek üzeresiniz. Bu araç artık listelerde varsayılan olarak görünmeyecek ancak verileri saklanacaktır.'
                                : ' tamamen silmek üzeresiniz. Bu işlem geri alınamaz ve tüm geçmiş verileri kaybolacaktır.'}
                        </p>

                        <div className="flex gap-3">
                            <Button variant="secondary" onClick={onClose} className="flex-1 h-12 text-base">
                                İptal
                            </Button>
                            <Button
                                variant="danger"
                                onClick={async () => {
                                    await onConfirm()
                                    onClose()
                                }}
                                className={`flex-1 h-12 text-base ${isSoftDelete ? 'bg-warning hover:bg-warning/80 text-bg-base' : ''}`}
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
