import { useState, useRef, useEffect } from 'react'
import { FileSpreadsheet, Download, Upload, RefreshCw, ChevronDown } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'
import { ExcelUploadModal } from './ExcelUploadModal'
import { RequirePermission } from '../auth/RequirePermission'

interface DataExportImportProps {
    onExport?: () => Promise<void>
    onImport?: (file: File) => Promise<any>
    onImportSuccess?: () => void
    onDownloadTemplate?: () => Promise<void>
    variant?: 'toolbar' | 'dropdown'
    className?: string
}

export function DataExportImport({
    onExport,
    onImport,
    onImportSuccess,
    onDownloadTemplate,
    variant = 'toolbar',
    className
}: DataExportImportProps) {
    const [isExporting, setIsExporting] = useState(false)
    const [isTemplateDownloading, setIsTemplateDownloading] = useState(false)
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
    const [isMenuOpen, setIsMenuOpen] = useState(false)
    const containerRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsMenuOpen(false)
            }
        }
        document.addEventListener("mousedown", handleClickOutside)
        return () => {
            document.removeEventListener("mousedown", handleClickOutside)
        }
    }, [containerRef])

    const handleExport = async () => {
        if (!onExport) return
        setIsExporting(true)
        try {
            await onExport()
        } finally {
            setIsExporting(false)
        }
    }



    const processFile = async (file: File) => {
        if (!onImport) return

        // Basic validation for Excel files
        const allowedExtensions = ['.xlsx', '.xls'];
        const fileName = file.name.toLowerCase();
        if (!allowedExtensions.some(ext => fileName.endsWith(ext))) {
            return; // In a real app we'd show a toast here, but onImport usually handles its own errors
        }


        try {
            const res = await onImport(file)
            if (onImportSuccess) {
                onImportSuccess()
            }
            return res
        } finally {
            // No-op
        }
    }



    const handleDownloadTemplate = async () => {
        if (!onDownloadTemplate) return
        setIsTemplateDownloading(true)
        try {
            await onDownloadTemplate()
        } finally {
            setIsTemplateDownloading(false)
        }
    }

    return (
        <div ref={containerRef} className={cn("relative", className)}>
            {variant === 'toolbar' ? (
                <Button
                    variant="ghost"
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    className={cn(
                        "h-[38px] px-4 rounded-xl border border-white/10 font-bold flex items-center gap-2 bg-black/20 text-slate-300 hover:text-white hover:bg-white/5 transition-all shadow-sm group",
                        isMenuOpen && "border-[#25d1f4]/50 text-[#25d1f4]"
                    )}
                >
                    <ChevronDown className={cn("w-4 h-4 transition-transform", isMenuOpen && "rotate-180")} />
                    Excel İşlemleri
                </Button>
            ) : null}

            <AnimatePresence>
                {(variant === 'dropdown' || isMenuOpen) && (
                    <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                        className={cn(
                            "glass-card border border-white/10 shadow-2xl overflow-hidden min-w-[240px] z-[100]",
                            variant === 'toolbar' ? "absolute right-0 top-full mt-2" : "w-full"
                        )}
                    >
                        {onImport && (
                            <RequirePermission permission="sefer:write">
                                <button
                                    onClick={() => {
                                        setIsUploadModalOpen(true)
                                        setIsMenuOpen(false)
                                    }}
                                    className="w-full px-5 py-4 text-left hover:bg-white/5 flex items-center gap-4 transition-all group border-b border-white/5"
                                >
                                    <div className="w-10 h-10 rounded-xl bg-[#25d1f4]/10 flex items-center justify-center text-[#25d1f4] group-hover:bg-[#25d1f4] group-hover:text-black transition-all transform group-hover:scale-110">
                                        <Upload className="w-5 h-5" />
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-sm font-black text-white tracking-tight">Excel'den Yükle</span>
                                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Dosya sürükleyerek içe aktar</span>
                                    </div>
                                </button>
                            </RequirePermission>
                        )}
                        
                        {onDownloadTemplate && (
                            <button
                                onClick={() => {
                                    handleDownloadTemplate()
                                    setIsMenuOpen(false)
                                }}
                                disabled={isTemplateDownloading}
                                className="w-full px-5 py-4 text-left hover:bg-white/5 flex items-center gap-4 transition-all group border-b border-white/5 disabled:opacity-50"
                            >
                                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 group-hover:bg-emerald-500 group-hover:text-black transition-all transform group-hover:scale-110">
                                    {isTemplateDownloading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <FileSpreadsheet className="w-5 h-5" />}
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-sm font-black text-white tracking-tight">Örnek Şablon</span>
                                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Excel şablonunu indir</span>
                                </div>
                            </button>
                        )}

                        {onExport && (
                            <button
                                onClick={() => {
                                    handleExport()
                                    setIsMenuOpen(false)
                                }}
                                disabled={isExporting}
                                className="w-full px-5 py-4 text-left hover:bg-white/5 flex items-center gap-4 transition-all group disabled:opacity-50"
                            >
                                <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400 group-hover:bg-blue-500 group-hover:text-black transition-all transform group-hover:scale-110">
                                    {isExporting ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />}
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-sm font-black text-white tracking-tight">Dışa Aktar</span>
                                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Tüm kayıtları Excel'e aktar</span>
                                </div>
                            </button>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Standalone Upload Modal */}
            <ExcelUploadModal
                isOpen={isUploadModalOpen}
                onClose={() => setIsUploadModalOpen(false)}
                onUpload={processFile}
            />
        </div>
    )
}
