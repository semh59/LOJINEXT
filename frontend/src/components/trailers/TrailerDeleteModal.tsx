import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trash2 } from 'lucide-react';
import { Dorse } from '../../types';

interface TrailerDeleteModalProps {
    trailer: Dorse | null;
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    isDeleting?: boolean;
}

const TrailerDeleteModal: React.FC<TrailerDeleteModalProps> = ({ 
    trailer, 
    isOpen, 
    onClose, 
    onConfirm,
    isDeleting = false
}) => {
    if (!trailer) return null;

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
                    />

                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="relative w-full max-w-md overflow-hidden bg-surface border border-border rounded-[2.5rem] shadow-2xl p-8 text-center"
                    >
                        <div className="w-20 h-20 bg-danger/10 border border-danger/20 rounded-3xl flex items-center justify-center text-danger mx-auto mb-6 shadow-danger/10">
                            <Trash2 size={40} />
                        </div>

                        <h2 className="text-2xl font-bold text-primary mb-3">Dorse Silinsin mi?</h2>
                        <p className="text-secondary mb-8 leading-relaxed">
                            <span className="text-danger font-bold">{trailer.plaka}</span> plakalı dorseyi silmek istediğinize emin misiniz? Bu işlem geri alınamaz.
                        </p>

                        <div className="flex flex-col gap-3">
                            <button
                                onClick={onConfirm}
                                disabled={isDeleting}
                                className="w-full py-4 rounded-2xl bg-danger hover:bg-danger/80 active:scale-95 text-bg-base font-bold transition-all shadow-lg shadow-danger/20 disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {isDeleting ? (
                                    <div className="w-5 h-5 border-2 border-bg-base/30 border-t-bg-base rounded-full animate-spin" />
                                ) : (
                                    'Dorseyi Kalıcı Olarak Sil'
                                )}
                            </button>
                            <button
                                onClick={onClose}
                                disabled={isDeleting}
                                className="w-full py-4 rounded-2xl bg-bg-elevated hover:bg-surface border border-border text-secondary font-bold transition-all"
                            >
                                Vazgeç
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
};

export default TrailerDeleteModal;
