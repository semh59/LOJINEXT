import * as React from "react"
import { cn } from "../../lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
    variant?: "default" | "success" | "warning" | "error"
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
    const variants = {
        default: "bg-slate-100 text-slate-700 hover:bg-slate-200/80",
        success: "bg-emerald-100 text-emerald-700 hover:bg-emerald-200/80",
        warning: "bg-amber-100 text-amber-700 hover:bg-amber-200/80",
        error: "bg-red-100 text-red-700 hover:bg-red-200/80",
    }

    return (
        <div
            className={cn(
                "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2",
                variants[variant],
                "border-transparent",
                className
            )}
            {...props}
        />
    )
}

export { Badge }
