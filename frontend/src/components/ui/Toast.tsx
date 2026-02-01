import { motion } from "framer-motion"
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react"
import { cn } from "../../lib/utils"

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface ToastProps {
    id: string
    type: ToastType
    title: string
    message?: string
    onClose: (id: string) => void
}

export function Toast({ id, type, title, message, onClose }: ToastProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
            layout
            className={cn(
                "pointer-events-auto w-full glass p-4 rounded-2xl border shadow-floating flex gap-4 items-start relative overflow-hidden group mb-3",
                type === 'success' && "border-emerald-500/20 bg-emerald-500/5",
                type === 'error' && "border-red-500/20 bg-red-500/5",
                type === 'warning' && "border-amber-500/20 bg-amber-500/5",
                type === 'info' && "border-blue-500/20 bg-blue-500/5"
            )}
        >
            <div className={cn(
                "p-2 rounded-xl flex-shrink-0",
                type === 'success' && "bg-emerald-500/10 text-emerald-600",
                type === 'error' && "bg-red-500/10 text-red-600",
                type === 'warning' && "bg-amber-500/10 text-amber-600",
                type === 'info' && "bg-blue-500/10 text-blue-600"
            )}>
                {type === 'success' && <CheckCircle size={18} />}
                {type === 'error' && <AlertCircle size={18} />}
                {type === 'warning' && <AlertTriangle size={18} />}
                {type === 'info' && <Info size={18} />}
            </div>

            <div className="flex-1 pr-6">
                <h4 className="text-sm font-bold text-neutral-800 leading-tight mb-1">{title}</h4>
                {message && <p className="text-xs text-neutral-500 font-medium leading-relaxed">{message}</p>}
            </div>

            <button
                onClick={() => onClose(id)}
                className="absolute top-3 right-3 p-1 rounded-lg hover:bg-neutral-100 text-neutral-400 transition-colors"
            >
                <X size={14} />
            </button>

            {/* Progress Bar */}
            <motion.div
                initial={{ width: "100%" }}
                animate={{ width: "0%" }}
                transition={{ duration: 5, ease: "linear" }}
                className={cn(
                    "absolute bottom-0 left-0 h-1 opacity-20",
                    type === 'success' && "bg-emerald-500",
                    type === 'error' && "bg-red-500",
                    type === 'warning' && "bg-amber-500",
                    type === 'info' && "bg-blue-500"
                )}
            />
        </motion.div>
    )
}
