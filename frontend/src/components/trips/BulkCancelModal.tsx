import React from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { XCircle, AlertTriangle } from 'lucide-react';

interface BulkCancelModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (reason: string) => void;
    selectedCount: number;
    isSubmitting: boolean;
}

export function BulkCancelModal({
    isOpen,
    onClose,
    onConfirm,
    selectedCount,
    isSubmitting
}: BulkCancelModalProps) {
    const [reason, setReason] = React.useState('');

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Toplu Sefer İptali"
            size="md"
        >
            <div className="space-y-6 py-2">
                <div className="bg-danger/10 p-4 rounded-2xl border border-danger/20 flex items-center gap-4">
                    <div className="w-10 h-10 bg-danger/20 rounded-xl flex items-center justify-center">
                        <XCircle className="w-6 h-6 text-danger" />
                    </div>
                    <div>
                        <h4 className="text-primary font-bold">{selectedCount} Sefer İptal Edilecek</h4>
                        <p className="text-secondary text-xs">Bu işlem geri alınamaz (ancak manuel olarak tekrar planlanabilir).</p>
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-xs font-bold text-secondary uppercase tracking-widest ml-1">İptal Nedeni (Zorunlu)</label>
                    <textarea
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        placeholder="Örn: Araç arızası, Müşteri iptali..."
                        className="w-full h-32 bg-bg-elevated/10 border border-border rounded-xl p-4 text-primary placeholder:text-secondary/40 focus:ring-2 focus:ring-danger/50 outline-none transition-all resize-none font-medium"
                    />
                    <div className="flex items-center gap-2 text-danger/70 ml-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span className="text-[10px] font-bold italic">Neden paylaşmadan iptal edilemez.</span>
                    </div>
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-border">
                    <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>Vazgeç</Button>
                    <Button 
                        variant="primary" 
                        onClick={() => onConfirm(reason)}
                        isLoading={isSubmitting}
                        disabled={reason.length < 5}
                        className="px-8 bg-danger hover:bg-danger/80 border-none shadow-[0_4px_20px_rgba(239,68,68,0.3)] shadow-danger/20"
                    >
                        İptal Et
                    </Button>
                </div>
            </div>
        </Modal>
    );
}
