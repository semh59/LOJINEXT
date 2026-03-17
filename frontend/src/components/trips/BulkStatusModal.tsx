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
    { value: 'Bekliyor', label: 'Bekliyor', color: 'bg-secondary' },
    { value: 'Planlandı', label: 'Planlandı', color: 'bg-warning' },
    { value: 'Yolda', label: 'Yolda', color: 'bg-accent' },
    { value: 'Devam Ediyor', label: 'Devam Ediyor', color: 'bg-accent/60' },
    { value: 'Tamamlandı', label: 'Tamamlandı', color: 'bg-success' },
    { value: 'Tamam', label: 'Tamam', color: 'bg-success' }
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
                <div className="bg-bg-elevated/20 p-4 rounded-2xl border border-border flex items-center gap-4">
                    <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center">
                        <Clock className="w-6 h-6 text-accent" />
                    </div>
                    <div>
                        <h4 className="text-primary font-bold">{selectedCount} Sefer Seçildi</h4>
                        <p className="text-secondary text-xs">Seçili tüm seferlerin durumunu toplu olarak güncelleyin.</p>
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
                                    ? "bg-bg-elevated border-accent/50 shadow-lg shadow-accent/5"
                                    : "bg-surface/50 border-border hover:border-accent/20 text-secondary"
                            )}
                        >
                            <div className={cn("w-3 h-3 rounded-full", opt.color)} />
                            <span className={cn("font-bold", selectedStatus === opt.value ? "text-primary" : "text-secondary")}>
                                {opt.label}
                            </span>
                        </button>
                    ))}
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-border">
                    <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>Vazgeç</Button>
                    <Button 
                        variant="primary" 
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
