import { Plus } from 'lucide-react'
import { DataExportImport } from '../shared/DataExportImport'
import { Button } from '../ui/Button'

interface FuelHeaderProps {
    onAdd: () => void
    onExport: () => Promise<void>
    onDownloadTemplate: () => Promise<void>
    onImport: (file: File) => Promise<void>
}

export function FuelHeader({ onAdd, onExport, onDownloadTemplate, onImport }: FuelHeaderProps) {
    return (
        <div className="flex justify-end mb-8 relative z-40">
            <div className="flex items-center gap-3">
                <DataExportImport
                    variant="toolbar"
                    onExport={onExport}
                    onDownloadTemplate={onDownloadTemplate}
                    onImport={onImport}
                />
                <Button
                    onClick={onAdd}
                    variant="glossy-green"
                    className="px-6 h-10 text-sm"
                >
                    <Plus className="w-5 h-5" /> Yeni Kayıt Ekle
                </Button>
            </div>
        </div>
    )
}
