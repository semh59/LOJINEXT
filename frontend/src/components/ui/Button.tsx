import * as React from "react"

import { Loader2 } from "lucide-react"
import { cn } from "../../lib/utils"

export interface ButtonProps
    extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "primary" | "secondary" | "danger" | "ghost" | "outline" | "glossy-cyan" | "glossy-purple" | "glossy-green" | "glossy-orange"
    size?: "sm" | "md" | "lg" | "icon"
    isLoading?: boolean
    asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = "primary", size = "md", isLoading, children, disabled, ...props }, ref) => {
        const Comp = "button"

        const variants = {
            primary: "btn-primary",
            secondary: "btn-secondary",
            danger: "btn-danger",
            ghost: "text-neutral-600 hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-800",
            outline: "border border-neutral-200 bg-transparent hover:bg-neutral-100 text-neutral-900 dark:border-neutral-800 dark:text-neutral-100",
            "glossy-cyan": "btn-glossy btn-glossy-cyan",
            "glossy-purple": "btn-glossy btn-glossy-purple",
            "glossy-green": "btn-glossy btn-glossy-green",
            "glossy-orange": "btn-glossy btn-glossy-orange",
        }

        const isGlossy = variant?.startsWith("glossy-")

        const sizes = {
            sm: "h-8 px-3 text-xs",
            md: "h-10 px-4 py-2",
            lg: "h-12 px-8 text-base",
            icon: "h-9 w-9 p-0 flex items-center justify-center",
        }

        return (
            <Comp
                className={cn(
                    "btn",
                    variants[variant],
                    sizes[size],
                    isLoading && "opacity-70 cursor-not-allowed",
                    className
                )}
                ref={ref}
                disabled={isLoading || disabled}
                {...props}
            >
                {isGlossy && <span className="glass-reflection" />}
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {children}
            </Comp>
        )
    }
)
Button.displayName = "Button"

export { Button }
