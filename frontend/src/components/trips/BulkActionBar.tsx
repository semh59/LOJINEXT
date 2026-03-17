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
                <div className="bg-surface/90 backdrop-blur-xl border border-accent/40 shadow-2xl p-4 rounded-[24px] flex items-center justify-between gap-6">
                    <div className="flex items-center gap-4">
                        <button 
                            onClick={onClear}
                            className="p-2 rounded-full hover:bg-bg-elevated text-secondary hover:text-primary transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                        <div className="flex flex-col">
                            <span className="text-accent font-black text-lg leading-none">{selectedCount}</span>
                            <span className="text-secondary text-[10px] font-bold uppercase tracking-wider">Seçili Sefer</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <RequirePermission permission="sefer:write">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={onStatusUpdate}
                                className="rounded-xl border-border hover:border-accent/50 text-secondary hover:text-accent gap-2"
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
                                className="rounded-xl border-danger/20 hover:border-danger/50 text-secondary hover:text-danger gap-2"
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
                                className="rounded-xl bg-danger/10 hover:bg-danger/20 text-danger gap-2 border-none"
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
