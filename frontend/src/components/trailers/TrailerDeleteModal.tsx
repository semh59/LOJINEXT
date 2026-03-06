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
                        className="absolute inset-0 bg-black/80 backdrop-blur-md"
                    />

                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="relative w-full max-w-md overflow-hidden bg-slate-900 border border-slate-800 rounded-[2.5rem] shadow-2xl p-8 text-center"
                    >
                        <div className="w-20 h-20 bg-rose-500/10 border border-rose-500/20 rounded-3xl flex items-center justify-center text-rose-500 mx-auto mb-6 shadow-[0_0_30px_rgba(244,63,94,0.1)]">
                            <Trash2 size={40} />
                        </div>

                        <h2 className="text-2xl font-bold text-white mb-3">Dorse Silinsin mi?</h2>
                        <p className="text-slate-400 mb-8 leading-relaxed">
                            <span className="text-rose-400 font-bold">{trailer.plaka}</span> plakalı dorseyi silmek istediğinize emin misiniz? Bu işlem geri alınamaz.
                        </p>

                        <div className="flex flex-col gap-3">
                            <button
                                onClick={onConfirm}
                                disabled={isDeleting}
                                className="w-full py-4 rounded-2xl bg-rose-500 hover:bg-rose-600 active:scale-95 text-white font-bold transition-all shadow-lg shadow-rose-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {isDeleting ? (
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                ) : (
                                    'Dorseyi Kalıcı Olarak Sil'
                                )}
                            </button>
                            <button
                                onClick={onClose}
                                disabled={isDeleting}
                                className="w-full py-4 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold transition-all"
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
