import React from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Clock } from 'lucide-react';
import { cn } from '../../lib/utils';

interface BulkStatusModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (status: string) => void;
    selectedCount: number;
    isSubmitting: boolean;
}

const statusOptions = [
    { value: 'Planlandı', label: 'Planlandı', color: 'bg-[#f59e0b]' },
    { value: 'Yolda', label: 'Yolda / Devam Ediyor', color: 'bg-[#25d1f4]' },
    { value: 'Tamam', label: 'Tamamlandı', color: 'bg-[#10b981]' }
];

export function BulkStatusModal({
    isOpen,
    onClose,
    onConfirm,
    selectedCount,
    isSubmitting
}: BulkStatusModalProps) {
    const [selectedStatus, setSelectedStatus] = React.useState('Tamam');

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Toplu Durum Güncelle"
            size="md"
        >
            <div className="space-y-6 py-2">
                <div className="bg-[#132326]/50 p-4 rounded-2xl border border-[#25d1f4]/20 flex items-center gap-4">
                    <div className="w-10 h-10 bg-[#25d1f4]/10 rounded-xl flex items-center justify-center">
                        <Clock className="w-6 h-6 text-[#25d1f4]" />
                    </div>
                    <div>
                        <h4 className="text-white font-bold">{selectedCount} Sefer Seçildi</h4>
                        <p className="text-slate-400 text-xs">Seçili tüm seferlerin durumunu toplu olarak güncelleyin.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-2">
                    {statusOptions.map((opt) => (
                        <button
                            key={opt.value}
                            onClick={() => setSelectedStatus(opt.value)}
                            className={cn(
                                "flex items-center gap-3 p-4 rounded-xl border transition-all text-left",
                                selectedStatus === opt.value
                                    ? "bg-white/5 border-[#25d1f4]/50 shadow-[0_0_15px_rgba(37,209,244,0.1)]"
                                    : "bg-transparent border-white/5 hover:border-white/20 text-slate-400"
                            )}
                        >
                            <div className={cn("w-3 h-3 rounded-full", opt.color)} />
                            <span className={cn("font-bold", selectedStatus === opt.value ? "text-white" : "text-slate-400")}>
                                {opt.label}
                            </span>
                        </button>
                    ))}
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                    <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>Vazgeç</Button>
                    <Button 
                        variant="glossy-cyan" 
                        onClick={() => onConfirm(selectedStatus)}
                        isLoading={isSubmitting}
                        className="px-8"
                    >
                        Güncelle
                    </Button>
                </div>
            </div>
        </Modal>
    );
}
