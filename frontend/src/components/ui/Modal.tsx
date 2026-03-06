import * as React from "react"
import { createPortal } from "react-dom"
import { X } from "lucide-react"
import { cn } from "../../lib/utils"

interface ModalProps {
    isOpen: boolean
    onClose: () => void
    title?: React.ReactNode
    children: React.ReactNode
    size?: 'sm' | 'md' | 'lg' | 'xl'
    className?: string
}

export function Modal({ isOpen, onClose, title, children, size = 'md', className }: ModalProps) {
    // Esc tuşu ve body scroll lock için effect her zaman çalışmalı (isOpen kontrolü içeride)
    React.useEffect(() => {
        if (!isOpen) return;

        document.body.style.overflow = 'hidden';

        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose()
        }
        document.addEventListener('keydown', handleEscape)
        
        return () => {
            document.removeEventListener('keydown', handleEscape);
            document.body.style.overflow = 'unset';
        }
    }, [isOpen, onClose])

    if (!isOpen) return null

    const sizeClasses = {
        sm: 'max-w-md',
        md: 'max-w-xl',
        lg: 'max-w-3xl',
        xl: 'max-w-5xl'
    }

    return createPortal(
        <div
            className="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200"
            onClick={(e) => e.target === e.currentTarget && onClose()}
        >
            <div
                className={cn(
                    "relative w-full rounded-3xl bg-white p-8 shadow-2xl animate-in zoom-in-95 duration-200 border border-white/20",
                    "max-h-[90vh] overflow-y-auto",
                    sizeClasses[size],
                    className
                )}
                role="dialog"
                aria-modal="true"
            >
                <button
                    onClick={onClose}
                    className="absolute right-6 top-6 rounded-full p-2 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-600 transition-colors z-10 bg-white/80 backdrop-blur-sm"
                >
                    <X className="h-5 w-5" />
                    <span className="sr-only">Close</span>
                </button>

                {title && (
                    <div className="mb-6 pr-10">
                        <h2 className="text-xl font-bold text-slate-900">{title}</h2>
                    </div>
                )}

                <div className="text-slate-600">
                    {children}
                </div>
            </div>
        </div>,
        document.body
    )
}

