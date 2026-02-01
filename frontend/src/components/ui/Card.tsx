import { ReactNode } from 'react'
import { cn } from '../../lib/utils'

interface CardProps {
    children: ReactNode
    className?: string
    padding?: 'none' | 'sm' | 'md' | 'lg'
}

export function Card({ children, className, padding = 'md' }: CardProps) {
    const paddingStyles = {
        none: 'p-0',
        sm: 'p-4',
        md: 'p-6',
        lg: 'p-8'
    }

    return (
        <div className={cn(
            "rounded-2xl bg-white/70 backdrop-blur-md border border-white/20 shadow-premium transition-all duration-300 hover:shadow-floating hover:-translate-y-1",
            paddingStyles[padding],
            className
        )}>
            {children}
        </div>
    )
}
