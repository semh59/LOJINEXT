import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    X, 
    Truck, 
    Calendar, 
    Hash, 
    Weight, 
    Settings, 
    Info, 
    Tractor,
    CircleDot
} from 'lucide-react';
import { Dorse } from '../../types';

interface TrailerDetailModalProps {
    trailer: Dorse | null;
    onClose: () => void;
}

const TrailerDetailModal: React.FC<TrailerDetailModalProps> = ({ trailer, onClose }) => {
    const [activeTab, setActiveTab] = React.useState<'general' | 'technical' | 'maintenance'>('general');

    if (!trailer) return null;

    const tabs = [
        { id: 'general', label: 'Genel Bakış', icon: Info },
        { id: 'technical', label: 'Teknik Özellikler', icon: Settings },
        { id: 'maintenance', label: 'Bakım Geçmişi', icon: Truck },
    ];

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
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
                    className="relative w-full max-w-4xl overflow-hidden bg-surface border border-border rounded-3xl shadow-2xl"
                >
                    {/* Header */}
                    <div className="relative h-48 bg-gradient-to-br from-accent/20 to-accent/5 p-8 flex items-end">
                        <div className="absolute top-6 right-6">
                            <button
                                onClick={onClose}
                                className="p-2 hover:bg-bg-elevated rounded-xl transition-colors text-secondary hover:text-primary"
                            >
                                <X size={24} />
                            </button>
                        </div>

                        <div className="flex items-center gap-6">
                            <div className="w-24 h-24 rounded-2xl bg-accent/20 border border-accent/30 flex items-center justify-center text-accent shrink-0">
                                <Tractor size={48} />
                            </div>
                            <div>
                                <h2 className="text-3xl font-bold text-primary tracking-tight">{trailer.plaka}</h2>
                                <p className="text-accent font-medium">{trailer.marka} {trailer.model}</p>
                            </div>
                        </div>

                        {/* Status Badge */}
                        <div className="absolute bottom-8 right-8">
                            <div className={`px-4 py-1.5 rounded-full text-xs font-bold tracking-wider uppercase border ${
                                trailer.aktif 
                                    ? 'bg-success/10 border-success/30 text-success' 
                                    : 'bg-danger/10 border-danger/30 text-danger'
                            }`}>
                                {trailer.aktif ? 'AKTİF' : 'PASİF'}
                            </div>
                        </div>
                    </div>

                    {/* Tabs Navigation */}
                    <div className="flex border-b border-border px-8">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={`flex items-center gap-2 px-6 py-4 text-sm font-medium transition-all relative ${
                                    activeTab === tab.id ? 'text-accent' : 'text-secondary hover:text-primary'
                                }`}
                            >
                                <tab.icon size={18} />
                                {tab.label}
                                {activeTab === tab.id && (
                                    <motion.div
                                        layoutId="activeTab"
                                        className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent shadow-[0_0_10px_rgba(var(--accent-rgb),0.5)]"
                                    />
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Content */}
                    <div className="p-8 max-h-[500px] overflow-y-auto custom-scrollbar">
                        {activeTab === 'general' && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-6">
                                    <h3 className="text-xs font-bold text-secondary uppercase tracking-widest px-1">Temel Bilgiler</h3>
                                    <div className="grid grid-cols-1 gap-4">
                                        <InfoCard icon={Hash} label="Plaka" value={trailer.plaka} />
                                        <InfoCard icon={Truck} label="Marka / Model" value={`${trailer.marka} ${trailer.model || '-'}`} />
                                        <InfoCard icon={Calendar} label="Model Yılı" value={trailer.yil?.toString() || '-'} />
                                    </div>
                                </div>
                                <div className="space-y-6">
                                    <h3 className="text-xs font-bold text-secondary uppercase tracking-widest px-1">Operasyonel Durum</h3>
                                    <div className="grid grid-cols-1 gap-4">
                                        <InfoCard icon={CircleDot} label="Tip" value={trailer.dorse_tipi || 'Belirtilmemiş'} />
                                        <InfoCard icon={Info} label="Notlar" value={trailer.notlar || '-'} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'technical' && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-6">
                                    <h3 className="text-xs font-bold text-secondary uppercase tracking-widest px-1">Ağırlık & Kapasite</h3>
                                    <div className="grid grid-cols-1 gap-4">
                                        <InfoCard icon={Weight} label="Boş Ağırlık" value={`${trailer.bos_agirlik_kg?.toLocaleString()} kg`} />
                                        <InfoCard icon={CircleDot} label="Lastik Sayısı" value={trailer.lastik_sayisi?.toString() || '6'} />
                                    </div>
                                </div>
                                <div className="space-y-6">
                                    <h3 className="text-xs font-bold text-secondary uppercase tracking-widest px-1">Fiziksel Parametreler</h3>
                                    <div className="grid grid-cols-1 gap-4">
                                        <InfoCard icon={CircleDot} label="Rolling Resistance" value={trailer.rolling_resistance?.toString() || '0.006'} />
                                        <InfoCard icon={CircleDot} label="Drag Coefficient" value={trailer.drag_coefficient?.toString() || '0.75'} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'maintenance' && (
                            <div className="flex flex-col items-center justify-center py-12 text-secondary border-2 border-dashed border-border rounded-3xl bg-bg-elevated/5">
                                <Truck size={48} className="mb-4 opacity-20" />
                                <p className="font-medium">Yakında: Bakım kayıtları burada listelenecek.</p>
                                <p className="text-sm">Entegrasyon devam ediyor.</p>
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="p-6 bg-bg-elevated/20 border-t border-border flex justify-end gap-3">
                        <button
                            onClick={onClose}
                            className="px-6 py-2.5 rounded-xl border border-border text-secondary font-medium hover:bg-bg-elevated transition-all"
                        >
                            Kapat
                        </button>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};

const InfoCard = ({ icon: Icon, label, value }: { icon: any, label: string, value: string }) => (
    <div className="flex items-center gap-4 p-4 bg-bg-elevated/20 border border-border rounded-2xl group hover:bg-bg-elevated/40 transition-all">
        <div className="w-10 h-10 rounded-xl bg-bg-elevated border border-border flex items-center justify-center text-secondary group-hover:text-accent transition-colors">
            <Icon size={20} />
        </div>
        <div>
            <p className="text-xs font-medium text-secondary mb-0.5 uppercase tracking-wider">{label}</p>
            <p className="text-sm font-bold text-primary group-hover:text-accent transition-colors">{value}</p>
        </div>
    </div>
);

export default TrailerDetailModal;
