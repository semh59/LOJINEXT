import React from 'react';
import { Search, Calendar, FileSpreadsheet, Plus } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { useTripStore } from '../../stores/use-trip-store';

/**
 * Seferler filtreleme bileşeni
 */

interface TripFiltersProps {
    onExport: () => void;
    onAdd: () => void;
}

const DURUM_OPTIONS = [
    { label: 'Tüm Durumlar', value: '' },
    { label: 'Tamamlandı', value: 'Tamam' },
    { label: 'Devam Ediyor', value: 'Devam Ediyor' },
    { label: 'Bekliyor', value: 'Bekliyor' },
    { label: 'İptal', value: 'İptal' },
];

export const TripFilters: React.FC<TripFiltersProps> = ({ onExport, onAdd }) => {
    const { filters, setFilters } = useTripStore();

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFilters({ search: e.target.value });
    };

    const handleDateChange = (field: 'baslangic_tarih' | 'bitis_tarih', value: string) => {
        setFilters({ [field]: value });
    };

    const handleDurumChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setFilters({ durum: e.target.value });
    };

    return (
        <div className="flex flex-col xl:flex-row gap-4 bg-white/80 backdrop-blur-md p-4 rounded-3xl border border-slate-200/60 shadow-sm sticky top-0 z-20 mb-6">
            {/* Search Input */}
            <div className="relative flex-1 group">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                <Input
                    placeholder="Plaka, şoför veya şehir ara..."
                    value={filters.search}
                    onChange={handleSearchChange}
                    className="pl-11 pr-4 h-11 bg-slate-50/50 border-slate-200/80 rounded-2xl focus:ring-4 focus:ring-indigo-500/10 transition-all"
                />
            </div>

            {/* Filters & Actions */}
            <div className="flex flex-wrap items-center gap-3">
                {/* Date Picker Group */}
                <div className="flex items-center gap-2 bg-slate-50/80 p-1 rounded-2xl border border-slate-200/80">
                    <div className="relative px-3 flex items-center gap-2 border-r border-slate-200/80">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <input
                            type="date"
                            value={filters.baslangic_tarih || ''}
                            onChange={(e) => handleDateChange('baslangic_tarih', e.target.value)}
                            className="bg-transparent text-xs font-semibold text-slate-600 focus:outline-none h-9"
                        />
                    </div>
                    <div className="relative px-3 flex items-center gap-2">
                        <input
                            type="date"
                            value={filters.bitis_tarih || ''}
                            onChange={(e) => handleDateChange('bitis_tarih', e.target.value)}
                            className="bg-transparent text-xs font-semibold text-slate-600 focus:outline-none h-9"
                        />
                    </div>
                </div>

                {/* Status Filter */}
                <div className="flex items-center">
                    <select
                        value={filters.durum || ''}
                        onChange={handleDurumChange}
                        className="h-11 rounded-2xl border border-slate-200/80 bg-slate-50/50 px-3 text-sm font-medium text-slate-600 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all cursor-pointer"
                    >
                        {DURUM_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                    </select>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2 ml-auto">
                    <Button
                        variant="secondary"
                        size="md"
                        onClick={onExport}
                        className="h-11 rounded-2xl font-bold gap-2 px-5 bg-emerald-50 text-emerald-700 border-emerald-100 hover:bg-emerald-100"
                    >
                        <FileSpreadsheet className="w-4 h-4" />
                        Excel
                    </Button>
                    <Button
                        size="md"
                        onClick={onAdd}
                        className="h-11 rounded-2xl font-bold gap-2 px-6 shadow-lg shadow-indigo-500/20 bg-indigo-600 text-white hover:bg-indigo-700"
                    >
                        <Plus className="w-4 h-4" />
                        Yeni Sefer
                    </Button>
                </div>
            </div>
        </div>
    );
};
