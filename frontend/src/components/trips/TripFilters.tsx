import * as React from 'react';
import { cn } from '../../lib/utils';
import { Filter } from 'lucide-react';
import { Button } from '../ui/Button';
import { useTripStore } from '../../stores/use-trip-store';
import { DataExportImport } from '../shared/DataExportImport';
import { preferenceService, Preference } from '../../services/api/preference-service';
import { toast } from 'sonner';
import { Save, Bookmark, Trash2 as TrashIcon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface TripFiltersProps {
    onExport: () => Promise<void>;
    onImport: (file: File) => Promise<any>;
    onDownloadTemplate: () => Promise<void>;
}

const DURUM_TABS = [
    { label: 'Tümü', value: '' },
    { label: 'Devam Ediyor', value: 'Devam Ediyor' },
    { label: 'Planlandı', value: 'Planlandı' },
    { label: 'Tamamlandı', value: 'Tamam' },
];

export const TripFilters: React.FC<TripFiltersProps> = ({
    onExport,
    onImport,
    onDownloadTemplate
}) => {
    const { filters, setFilters, resetFilters } = useTripStore();
    const [savedFilters, setSavedFilters] = React.useState<Preference[]>([]);
    const [isSaving, setIsSaving] = React.useState(false);
    const [newFilterName, setNewFilterName] = React.useState('');
    const [showSaveInput, setShowSaveInput] = React.useState(false);

    const loadSavedFilters = async () => {
        try {
            const prefs = await preferenceService.getPreferences('seferler', 'filtre');
            setSavedFilters(prefs);
            
            // Apply default filter if exists and nothing is set yet
            const hasActiveFilters = Object.values(filters).some(v => v !== '' && v !== 0 && v !== undefined);
            if (!hasActiveFilters) {
                const defaultFilter = prefs.find(p => p.is_default);
                if (defaultFilter) {
                    setFilters(defaultFilter.deger);
                }
            }
        } catch (error) {
            console.error('Failed to load saved filters', error);
        }
    };

    React.useEffect(() => {
        loadSavedFilters();
    }, []);

    const handleSaveFilter = async () => {
        console.log('💾 [FILTER SAVE] Kayıt başlatıldı. Filtre Adı:', newFilterName, 'Değerler:', filters);
        if (!newFilterName.trim()) {
            toast.error('Lütfen filtre için bir isim girin.');
            return;
        }

        setIsSaving(true);
        try {
            const res = await preferenceService.savePreference({
                modul: 'seferler',
                ayar_tipi: 'filtre',
                ad: newFilterName,
                deger: filters,
                is_default: false
            });
            console.log('✅ [FILTER SAVE SUCCESS]:', res);
            toast.success('Filtre kaydedildi.');
            setNewFilterName('');
            setShowSaveInput(false);
            loadSavedFilters();
        } catch (error: any) {
            console.error('❌ [FILTER SAVE FAILED]:', error);
            const msg = error?.response?.data?.detail || error?.message || 'Filtre kaydedilirken hata oluştu.';
            toast.error(msg);
        } finally {
            setIsSaving(false);
        }
    };

    const handleDeleteFilter = async (id: number, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await preferenceService.deletePreference(id);
            toast.success('Filtre silindi.');
            loadSavedFilters();
        } catch (error) {
            toast.error('Filtre silinemedi.');
        }
    };

    return (
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            {/* Status Pills */}
            <div className="flex items-center gap-2 p-1.5 bg-black/20 rounded-2xl border border-white/5 backdrop-blur-md">
                {DURUM_TABS.map(tab => {
                    const isActive = filters.durum === tab.value;
                    return (
                        <button
                            key={tab.value}
                            onClick={() => setFilters({ durum: tab.value })}
                            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                                isActive
                                    ? 'bg-[#25d1f4]/10 text-[#25d1f4] shadow-[0_0_15px_rgba(37,209,244,0.1)] border border-[#25d1f4]/20'
                                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                            }`}
                        >
                            {tab.label}
                        </button>
                    );
                })}
            </div>

            {/* Saved Filters Shortcut */}
            {savedFilters.length > 0 && (
                <div className="flex items-center gap-2 overflow-x-auto pb-1 max-w-[400px] scrollbar-hide">
                    {savedFilters.map((pref) => (
                        <div
                            key={pref.id}
                            className="flex items-center group"
                        >
                            <button
                                onClick={() => setFilters(pref.deger)}
                                className={cn(
                                    "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border transition-all whitespace-nowrap",
                                    JSON.stringify(filters) === JSON.stringify(pref.deger)
                                        ? "bg-[#25d1f4]/10 border-[#25d1f4]/30 text-[#25d1f4]"
                                        : "bg-white/5 border-white/5 text-slate-400 hover:text-white hover:border-white/10"
                                )}
                            >
                                <Bookmark className="w-3 h-3" />
                                {pref.ad}
                            </button>
                            <button 
                                onClick={(e) => handleDeleteFilter(pref.id, e)}
                                className="w-0 overflow-hidden group-hover:w-6 group-hover:ml-1 transition-all text-slate-500 hover:text-red-400"
                            >
                                <TrashIcon className="w-3 h-3" />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Actions & Dates */}
            <div className="flex items-center gap-3 flex-wrap">
                <div className="flex items-center gap-2">
                    <input 
                        type="date"
                        value={filters.baslangic_tarih || ''}
                        onChange={(e) => setFilters({ baslangic_tarih: e.target.value })}
                        className="bg-black/20 border border-white/10 text-slate-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#25d1f4]/50 [&::-webkit-calendar-picker-indicator]:filter [&::-webkit-calendar-picker-indicator]:invert transition-colors"
                        title="Başlangıç Tarihi"
                    />
                    <span className="text-slate-500">-</span>
                    <input 
                        type="date"
                        value={filters.bitis_tarih || ''}
                        onChange={(e) => setFilters({ bitis_tarih: e.target.value })}
                        className="bg-black/20 border border-white/10 text-slate-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#25d1f4]/50 [&::-webkit-calendar-picker-indicator]:filter [&::-webkit-calendar-picker-indicator]:invert transition-colors"
                        title="Bitiş Tarihi"
                    />
                </div>
                
                <Button 
                    variant="ghost"
                    onClick={() => {
                        resetFilters();
                        toast.success('Filtreler sıfırlandı.');
                    }}
                    className="flex items-center gap-2 bg-black/20 border border-white/10 text-slate-300 hover:text-white hover:bg-white/5 rounded-xl h-[38px]"
                >
                    <Filter className="w-4 h-4" />
                    Sıfırla
                </Button>

                <div className="relative">
                    <Button
                        variant="ghost"
                        onClick={() => setShowSaveInput(!showSaveInput)}
                        className={cn(
                            "flex items-center gap-2 bg-black/20 border border-white/10 text-slate-300 hover:text-white hover:bg-white/5 rounded-xl h-[38px]",
                            showSaveInput && "border-[#25d1f4]/50 text-[#25d1f4]"
                        )}
                        title="Mevcut Filtreyi Kaydet"
                    >
                        <Save className="w-4 h-4" />
                    </Button>

                    <AnimatePresence>
                        {showSaveInput && (
                            <motion.div
                                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                className="absolute right-0 top-full mt-2 w-64 p-3 glass-card border border-white/10 shadow-2xl z-[60]"
                            >
                                <p className="text-xs font-bold text-slate-400 uppercase mb-2 tracking-wider">Filtre Adı</p>
                                <div className="flex flex-col gap-3">
                                    <input 
                                        autoFocus
                                        type="text"
                                        placeholder="Örn: Aktif Seferler"
                                        value={newFilterName}
                                        onChange={(e) => setNewFilterName(e.target.value)}
                                        className="bg-black/40 border border-white/10 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#25d1f4]/50"
                                        onKeyDown={(e) => e.key === 'Enter' && handleSaveFilter()}
                                    />
                                    <div className="flex gap-2">
                                        <Button 
                                            size="sm"
                                            className="flex-1 text-xs"
                                            onClick={handleSaveFilter}
                                            isLoading={isSaving}
                                        >
                                            Kaydet
                                        </Button>
                                        <Button 
                                            size="sm"
                                            variant="ghost"
                                            className="text-xs border border-white/5"
                                            onClick={() => setShowSaveInput(false)}
                                        >
                                            Vazgeç
                                        </Button>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
                
                <DataExportImport 
                    onExport={onExport}
                    onImport={onImport}
                    onDownloadTemplate={onDownloadTemplate}
                    variant="toolbar"
                />
            </div>
        </div>
    );
};
