
import { useState, useRef } from 'react'
import { X, Upload, FileSpreadsheet, CheckCircle, AlertCircle } from 'lucide-react'
import { vehiclesApi } from '../../services/api'
import { cn } from '../../lib/utils'

interface VehicleUploadModalProps {
    isOpen: boolean
    onClose: () => void
    onSuccess: () => void
}

export function VehicleUploadModal({ isOpen, onClose, onSuccess }: VehicleUploadModalProps) {
    const [file, setFile] = useState<File | null>(null)
    const [uploading, setUploading] = useState(false)
    const [result, setResult] = useState<{ message: string; errors?: string[] } | null>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const [isDragging, setIsDragging] = useState(false)

    if (!isOpen) return null

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            validateAndSetFile(e.target.files[0])
        }
    }

    const validateAndSetFile = (file: File) => {
        if (!file.name.match(/\.(xlsx|xls)$/)) {
            alert('Lütfen sadece Excel (.xlsx, .xls) dosyası yükleyin.')
            return
        }
        setFile(file)
        setResult(null)
    }

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(true)
    }

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            validateAndSetFile(e.dataTransfer.files[0])
        }
    }

    const handleUpload = async () => {
        if (!file) return

        setUploading(true)
        setResult(null)

        try {
            const response = await vehiclesApi.uploadExcel(file)
            setResult({
                message: response.message || 'Yükleme başarılı',
                errors: response.errors
            })
            if (!response.errors || response.errors.length === 0) {
                setTimeout(() => {
                    onSuccess()
                    onClose()
                    setFile(null)
                    setResult(null)
                }, 2000)
            }
        } catch (error: any) {
            console.error('Upload failed', error)
            setResult({
                message: 'Yükleme sırasında bir hata oluştu.',
                errors: [error.message || 'Bilinmeyen hata']
            })
        } finally {
            setUploading(false)
        }
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-white rounded-2xl shadow-modal w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-neutral-100 shrink-0">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-success-light/20 flex items-center justify-center text-success">
                            <FileSpreadsheet className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-neutral-800">Excel ile Yükle</h2>
                            <p className="text-sm text-neutral-500">Toplu araç yükleme</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-neutral-100 rounded-lg transition-colors text-neutral-400 hover:text-neutral-600"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="p-6 overflow-y-auto">
                    {!file ? (
                        <div
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                            className={cn(
                                "border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center gap-4 cursor-pointer transition-all group",
                                isDragging
                                    ? "border-brand bg-brand-light/10 scale-[1.02]"
                                    : "border-neutral-200 hover:border-brand hover:bg-brand-light/5"
                            )}
                        >
                            <div className={cn(
                                "w-16 h-16 rounded-full flex items-center justify-center transition-transform",
                                isDragging ? "bg-brand-light/20 scale-110" : "bg-neutral-50 group-hover:scale-110"
                            )}>
                                <Upload className={cn(
                                    "w-8 h-8 transition-colors",
                                    isDragging ? "text-brand" : "text-neutral-400 group-hover:text-brand"
                                )} />
                            </div>
                            <div className="text-center">
                                <p className="text-neutral-900 font-medium">
                                    {isDragging ? "Dosyayı buraya bırakın" : "Dosyayı buraya sürükleyin veya seçin"}
                                </p>
                                <p className="text-sm text-neutral-500 mt-1">Sadece .xlsx ve .xls dosyaları</p>
                            </div>
                            <input
                                type="file"
                                ref={fileInputRef}
                                className="hidden"
                                accept=".xlsx, .xls"
                                onChange={handleFileChange}
                            />
                        </div>
                    ) : (
                        <div className="space-y-6">
                            <div className="flex items-center gap-4 p-4 bg-neutral-50 rounded-xl border border-neutral-100">
                                <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center border border-neutral-200 shadow-sm">
                                    <FileSpreadsheet className="w-5 h-5 text-success" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-neutral-900 truncate">{file.name}</p>
                                    <p className="text-xs text-neutral-500">{(file.size / 1024).toFixed(1)} KB</p>
                                </div>
                                <button
                                    onClick={() => { setFile(null); setResult(null); }}
                                    className="p-2 hover:bg-white rounded-lg text-neutral-400 hover:text-danger transition-colors"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>

                            {/* Status Area */}
                            {result && (
                                <div className={cn(
                                    "p-4 rounded-xl border text-sm",
                                    result.errors && result.errors.length > 0
                                        ? "bg-danger-light/10 border-danger-light/20 text-danger-dark"
                                        : "bg-success-light/10 border-success-light/20 text-success-dark"
                                )}>
                                    <div className="flex items-start gap-3">
                                        {result.errors && result.errors.length > 0 ? (
                                            <AlertCircle className="w-5 h-5 shrink-0" />
                                        ) : (
                                            <CheckCircle className="w-5 h-5 shrink-0" />
                                        )}
                                        <div>
                                            <p className="font-medium">{result.message}</p>
                                            {result.errors && result.errors.length > 0 && (
                                                <ul className="mt-2 list-disc list-inside space-y-1 opacity-90 max-h-32 overflow-y-auto">
                                                    {result.errors.map((err, i) => (
                                                        <li key={i}>{err}</li>
                                                    ))}
                                                </ul>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer - Always Visible */}
                <div className="p-6 border-t border-neutral-100 bg-neutral-50/50 flex items-center justify-between shrink-0">
                    <button
                        onClick={async () => {
                            try {
                                const blob = await vehiclesApi.downloadTemplate()
                                const url = window.URL.createObjectURL(blob)
                                const a = document.createElement('a')
                                a.href = url
                                a.download = 'arac_yukleme_sablonu.xlsx'
                                document.body.appendChild(a)
                                a.click()
                                window.URL.revokeObjectURL(url)
                                document.body.removeChild(a)
                            } catch (error) {
                                console.error('Şablon indirme hatası:', error)
                                alert('Şablon indirilemedi.')
                            }
                        }}
                        className="text-sm font-medium text-brand hover:text-brand-dark flex items-center gap-1.5 transition-colors"
                    >
                        <FileSpreadsheet className="w-4 h-4" />
                        Örnek Şablonu İndir
                    </button>

                    <div className="flex gap-3">
                        <button
                            onClick={onClose}
                            className="px-6 py-2.5 rounded-xl text-neutral-600 hover:bg-neutral-100 font-medium transition-colors"
                        >
                            İptal
                        </button>
                        <button
                            onClick={handleUpload}
                            disabled={!file || uploading || (!!result && (!result.errors || result.errors.length === 0))}
                            className="px-6 py-2.5 rounded-xl bg-primary text-white font-medium hover:bg-primary-dark transition-colors shadow-lg shadow-primary/25 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                            {uploading ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    Yükleniyor...
                                </>
                            ) : (
                                <>
                                    <Upload className="w-4 h-4" />
                                    Yüklemeyi Başlat
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
