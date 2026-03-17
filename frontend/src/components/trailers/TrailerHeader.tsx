import { Plus } from 'lucide-react'
import { Button } from '../ui/Button'
import { motion } from 'framer-motion'
import { DataExportImport } from '../shared/DataExportImport'

interface TrailerHeaderProps {
    onAdd: () => void
    onExport: () => Promise<void>
    onImport: (file: File) => Promise<void>
    onDownloadTemplate: () => Promise<void>
}

export function TrailerHeader({ onAdd, onExport, onImport, onDownloadTemplate }: TrailerHeaderProps) {
    return (
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-8 relative z-40">
            <motion.div 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-1"
            >
                <h1 className="text-4xl font-black text-primary tracking-tight flex items-center gap-3">
                    Dorse <span className="text-accent">Yönetimi</span>
                </h1>
                <p className="text-secondary font-medium tracking-wide">
                    Filo dorselerini izleyin, teknik detayları ve durumları yönetin.
                </p>
            </motion.div>

            <motion.div 
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex flex-wrap items-center gap-3"
            >
                <DataExportImport 
                    onExport={onExport}
                    onDownloadTemplate={onDownloadTemplate}
                    onImport={onImport}
                />

                <Button
                    onClick={onAdd}
                    variant="primary"
                    size="lg"
                    className="h-12 px-6 rounded-2xl shadow-lg shadow-accent/20 hover:shadow-accent/40 transition-all active:scale-95"
                >
                    <Plus className="w-5 h-5 mr-2" />
                    Yeni Dorse Ekle
                </Button>
            </motion.div>
        </div>
    )
}

