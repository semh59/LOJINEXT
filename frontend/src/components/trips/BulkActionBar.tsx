import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, Trash2, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { RequirePermission } from '../auth/RequirePermission';

interface BulkActionBarProps {
    selectedCount: number;
    onClear: () => void;
    onStatusUpdate: () => void;
    onCancel: () => void;
    onDelete: () => void;
}

export function BulkActionBar({
    selectedCount,
    onClear,
    onStatusUpdate,
    onCancel,
    onDelete
}: BulkActionBarProps) {
    if (selectedCount === 0) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ y: 100, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: 100, opacity: 0 }}
                className="fixed bottom-8 left-1/2 -translate-x-1/2 z-[100] w-full max-w-2xl px-4"
            >
                <div className="glass-card bg-[#132326]/90 backdrop-blur-xl border border-[#25d1f4]/30 shadow-[0_20px_50px_rgba(0,0,0,0.5)] p-4 rounded-[24px] flex items-center justify-between gap-6">
                    <div className="flex items-center gap-4">
                        <button 
                            onClick={onClear}
                            className="p-2 rounded-full hover:bg-white/5 text-slate-400 hover:text-white transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                        <div className="flex flex-col">
                            <span className="text-[#25d1f4] font-black text-lg leading-none">{selectedCount}</span>
                            <span className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">Seçili Sefer</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <RequirePermission permission="sefer:write">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={onStatusUpdate}
                                className="rounded-xl border-[#25d1f4]/20 hover:border-[#25d1f4]/50 text-slate-200 hover:text-[#25d1f4] gap-2"
                            >
                                <CheckCircle className="w-4 h-4" />
                                Durum Güncelle
                            </Button>
                        </RequirePermission>

                        <RequirePermission permission="sefer:write">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={onCancel}
                                className="rounded-xl border-rose-500/20 hover:border-rose-500/50 text-slate-200 hover:text-rose-400 gap-2"
                            >
                                <XCircle className="w-4 h-4" />
                                İptal Et
                            </Button>
                        </RequirePermission>

                        <RequirePermission permission="sefer:delete">
                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={onDelete}
                                className="rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 gap-2 border-none"
                            >
                                <Trash2 className="w-4 h-4" />
                                Toplu Sil
                            </Button>
                        </RequirePermission>
                    </div>
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
