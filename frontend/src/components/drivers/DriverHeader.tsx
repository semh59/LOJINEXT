import { Plus } from 'lucide-react'
import { Button } from '../ui/Button'
import { DataExportImport } from '../shared/DataExportImport'

interface DriverHeaderProps {
    onAdd: () => void
    onExport: () => Promise<void>
    onDownloadTemplate: () => Promise<void>
    onImport: (file: File) => Promise<void>
}

export function DriverHeader({ onAdd, onExport, onDownloadTemplate, onImport }: DriverHeaderProps) {
    return (
        <div className="flex justify-end gap-6 relative z-40">
            <div className="flex flex-wrap items-center gap-3">
                <DataExportImport 
                    onExport={onExport}
                    onDownloadTemplate={onDownloadTemplate}
                    onImport={onImport}
                />
                <Button
                    onClick={onAdd}
                    variant="glossy-purple"
                    size="lg"
                    className="px-6 h-12"
                >
                    <Plus className="w-5 h-5" /> Yeni Şoför Ekle
                </Button>
            </div>
        </div>
    )
}
