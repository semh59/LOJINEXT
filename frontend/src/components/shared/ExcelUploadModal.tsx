import React, { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Upload, FileSpreadsheet, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'

interface ExcelUploadModalProps {
    isOpen: boolean
    onClose: () => void
    onUpload: (file: File) => Promise<any>
    title?: string
    description?: string
}

export function ExcelUploadModal({
    isOpen,
    onClose,
    onUpload,
    title = "Excel Kayıtlarını İçe Aktar",
    description = "Dosyanızı buraya sürükleyin veya seçmek için tıklayın (.xlsx, .xls)"
}: ExcelUploadModalProps) {
    const [isDragging, setIsDragging] = useState(false)
    const [file, setFile] = useState<File | null>(null)
    const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
    const [errorMessage, setErrorMessage] = useState<string | null>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)
    const [mounted, setMounted] = useState(false)

    useEffect(() => {
        setMounted(true)
        return () => setMounted(false)
    }, [])

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(true)
    }

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(false)
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(false)
        
        const droppedFile = e.dataTransfer.files?.[0]
        if (droppedFile) validateAndSetFile(droppedFile)
    }

    const validateAndSetFile = (selectedFile: File) => {
        const allowedExtensions = ['.xlsx', '.xls']
        const fileName = selectedFile.name.toLowerCase()
        
        if (!allowedExtensions.some(ext => fileName.endsWith(ext))) {
            setStatus('error')
            setErrorMessage('Lütfen sadece Excel (.xlsx, .xls) dosyası yükleyin.')
            return
        }

        setFile(selectedFile)
        setStatus('idle')
        setErrorMessage(null)
    }

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0]
        if (selectedFile) validateAndSetFile(selectedFile)
    }

    const [uploadResult, setUploadResult] = useState<{ processed?: number, saved?: number, errors?: any[] } | null>(null)

    const handleUpload = async () => {
        if (!file) return
        
        setStatus('uploading')
        setUploadResult(null)
        setErrorMessage(null)
        try {
            const res = await onUpload(file)
            
            // Check if there are errors returned in a 200 response
            if (res && res.errors && res.errors.length > 0) {
                setStatus('error')
                setUploadResult(res)
                return
            }

            setStatus('success')
            setTimeout(() => {
                onClose()
                resetState()
            }, 1500)
        } catch (error: any) {
            setStatus('error')
            setErrorMessage(error?.response?.data?.detail || error?.message || 'Yükleme sırasında bir hata oluştu.')
        }
    }

    const resetState = () => {
        setFile(null)
        setStatus('idle')
        setErrorMessage(null)
        setUploadResult(null)
    }

    if (!mounted) return null

    return createPortal(
        <AnimatePresence mode="wait">
            {isOpen && (
                <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-neutral-900/60 backdrop-blur-sm"
                    />
                    
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="relative w-full max-w-xl bg-white rounded-[32px] shadow-2xl overflow-hidden border border-neutral-100 z-10"
                    >
                        {/* Header */}
                        <div className="px-8 pt-8 pb-4 flex items-start justify-between">
                            <div>
                                <h2 className="text-2xl font-black text-neutral-900 tracking-tight">{title}</h2>
                                <p className="text-sm font-medium text-neutral-500 mt-1">{description}</p>
                            </div>
                            <button 
                                onClick={onClose}
                                className="p-2 hover:bg-neutral-100 rounded-xl transition-colors text-neutral-400 hover:text-neutral-900"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="p-8 space-y-6">
                            {/* Drop Zone */}
                            <div
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                                onDrop={handleDrop}
                                onClick={() => fileInputRef.current?.click()}
                                className={cn(
                                    "relative min-h-[220px] rounded-[24px] border-2 border-dashed transition-all cursor-pointer flex flex-col items-center justify-center text-center p-6 bg-neutral-50/50 hover:bg-neutral-50",
                                    isDragging ? "border-primary bg-primary/5 scale-[0.98]" : "border-neutral-200",
                                    file ? "border-emerald-300 bg-emerald-50/30" : ""
                                )}
                            >
                                <input 
                                    type="file" 
                                    ref={fileInputRef} 
                                    onChange={handleFileSelect} 
                                    accept=".xlsx,.xls" 
                                    className="hidden" 
                                />

                                <AnimatePresence mode="wait">
                                    {status === 'uploading' ? (
                                        <motion.div
                                            key="uploading"
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            exit={{ opacity: 0 }}
                                            className="flex flex-col items-center"
                                        >
                                            <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
                                            <span className="font-bold text-neutral-600">Dosya işleniyor...</span>
                                        </motion.div>
                                    ) : status === 'success' ? (
                                        <motion.div
                                            key="success"
                                            initial={{ opacity: 0, scale: 0.8 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            exit={{ opacity: 0 }}
                                            className="flex flex-col items-center"
                                        >
                                            <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-4">
                                                <CheckCircle2 className="w-8 h-8" />
                                            </div>
                                            <span className="font-bold text-emerald-700">Dosya başarıyla yüklendi!</span>
                                        </motion.div>
                                    ) : file ? (
                                        <motion.div
                                            key="file-selected"
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0 }}
                                            className="flex flex-col items-center"
                                        >
                                            <div className="w-16 h-16 bg-indigo-100 text-indigo-600 rounded-2xl flex items-center justify-center mb-4">
                                                <FileSpreadsheet className="w-8 h-8" />
                                            </div>
                                            <span className="font-bold text-neutral-900 truncate max-w-[300px]">{file.name}</span>
                                            <span className="text-xs font-medium text-neutral-400 mt-1">{(file.size / 1024).toFixed(1)} KB</span>
                                            <button 
                                                onClick={(e) => { e.stopPropagation(); resetState(); }}
                                                className="mt-4 text-xs font-bold text-rose-500 hover:text-rose-600 underline underline-offset-4"
                                            >
                                                Dosyayı Değiştir
                                            </button>
                                        </motion.div>
                                    ) : (
                                        <motion.div
                                            key="idle"
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            exit={{ opacity: 0 }}
                                            className="flex flex-col items-center"
                                        >
                                            <div className="w-16 h-16 bg-neutral-100 text-neutral-400 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-primary/10 group-hover:text-primary transition-all duration-300">
                                                <Upload className="w-8 h-8" />
                                            </div>
                                            <span className="font-bold text-neutral-700">Yüklemek için tıklayın veya sürükleyin</span>
                                            <span className="text-xs font-medium text-neutral-400 mt-1">Excel formats (.xlsx, .xls) allowed</span>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>

                            {/* Error Message */}
                            {status === 'error' && (
                                <motion.div
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="flex flex-col gap-3 p-4 bg-rose-50 text-rose-700 rounded-2xl border border-rose-100 text-sm font-medium max-h-64 overflow-y-auto custom-scrollbar"
                                >
                                    <div className="flex items-center gap-3">
                                         <AlertCircle className="w-5 h-5 shrink-0" />
                                         <span>{errorMessage || 'Dosya yüklenirken bazı hatalar tespit edildi.'}</span>
                                    </div>
                                    
                                    {uploadResult?.errors && uploadResult.errors.length > 0 && (
                                        <div className="mt-2 text-xs border border-rose-200 rounded-lg overflow-hidden flex-1">
                                            <table className="w-full text-left">
                                                <thead className="bg-rose-100/50">
                                                    <tr>
                                                        <th className="py-2 px-3 font-semibold w-16">Satır</th>
                                                        <th className="py-2 px-3 font-semibold w-24">Alan</th>
                                                        <th className="py-2 px-3 font-semibold">Hata Nedeni</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-rose-100 bg-white/50">
                                                    {uploadResult.errors.map((err: any, i: number) => (
                                                        <tr key={i}>
                                                            <td className="py-2 px-3">{err.row ?? typeof err === 'string' ? '-' : err.row}</td>
                                                            <td className="py-2 px-3 font-mono">{err.field || '-'}</td>
                                                            <td className="py-2 px-3 text-rose-600">{err.reason || typeof err === 'string' ? err : JSON.stringify(err)}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                    {uploadResult && (
                                        <div className="text-xs text-rose-600/80 mt-1 font-semibold flex justify-between">
                                            <span>İşlenen: {uploadResult.processed || 0}</span>
                                            <span>Başarılı: {uploadResult.saved || 0}</span>
                                            <span>Hatalı: {uploadResult.errors?.length || 0}</span>
                                        </div>
                                    )}
                                </motion.div>
                            )}

                            {/* Actions */}
                            <div className="flex items-center gap-4">
                                <Button
                                    onClick={onClose}
                                    variant="secondary"
                                    className="flex-1 h-12 rounded-2xl font-bold border-neutral-200 text-neutral-600 hover:bg-neutral-50 transition-all"
                                >
                                    İptal
                                </Button>
                                <Button
                                    onClick={handleUpload}
                                    disabled={!file || status === 'uploading' || status === 'success'}
                                    isLoading={status === 'uploading'}
                                    className="flex-[2] h-12 rounded-2xl font-bold shadow-xl shadow-primary/20 transition-all"
                                >
                                    Yüklemeyi Başlat
                                </Button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>,
        document.body
    )
}
