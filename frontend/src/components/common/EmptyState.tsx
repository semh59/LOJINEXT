import React from 'react';
import { Plus, LucideIcon, Inbox } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface EmptyStateProps {
    title: string;
    description: string;
    icon?: LucideIcon;
    actionLabel?: string;
    onAction?: () => void;
    className?: string;
}

const EmptyState: React.FC<EmptyStateProps> = ({
    title,
    description,
    icon: Icon = Inbox,
    actionLabel,
    onAction,
    className
}) => {
    return (
        <div className={cn(
            "flex flex-col items-center justify-center p-12 text-center bg-surface rounded-[32px] border-dashed border-2 border-border",
            className
        )}>
            <div className="w-24 h-24 bg-accent/10 rounded-full flex items-center justify-center mb-6 animate-pulse">
                <Icon className="w-12 h-12 text-accent" />
            </div>

            <h3 className="text-xl font-bold text-primary mb-2">
                {title}
            </h3>

            <p className="text-secondary max-w-xs mb-8 leading-relaxed">
                {description}
            </p>

            {actionLabel && onAction && (
                <button
                    onClick={onAction}
                    className="btn btn-primary group px-8"
                >
                    <Plus className="w-5 h-5 transition-transform group-hover:rotate-90" />
                    {actionLabel}
                </button>
            )}
        </div>
    );
};

export default EmptyState;
