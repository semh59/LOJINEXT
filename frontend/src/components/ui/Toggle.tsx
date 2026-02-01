import { cn } from "../../lib/utils"

export interface ToggleProps {
    checked: boolean
    onChange: (checked: boolean) => void
    label?: string
    disabled?: boolean
    size?: 'sm' | 'md'
    className?: string
}

export function Toggle({
    checked,
    onChange,
    label,
    disabled = false,
    size = 'md',
    className
}: ToggleProps) {
    const handleToggle = () => {
        if (!disabled) {
            onChange(!checked)
        }
    }

    const sizes = {
        sm: {
            track: 'w-8 h-4',
            thumb: 'w-3 h-3',
            translate: 'translate-x-4'
        },
        md: {
            track: 'w-11 h-6',
            thumb: 'w-5 h-5',
            translate: 'translate-x-5'
        }
    }

    return (
        <label
            className={cn(
                "inline-flex items-center gap-2 cursor-pointer select-none",
                disabled && "cursor-not-allowed opacity-50",
                className
            )}
        >
            <button
                type="button"
                role="switch"
                aria-checked={checked}
                disabled={disabled}
                onClick={handleToggle}
                className={cn(
                    "relative inline-flex shrink-0 rounded-full transition-colors duration-200 ease-in-out",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
                    sizes[size].track,
                    checked
                        ? "bg-primary"
                        : "bg-neutral-200"
                )}
            >
                <span
                    className={cn(
                        "pointer-events-none inline-block rounded-full bg-white shadow-lg ring-0 transition-transform duration-200 ease-in-out",
                        sizes[size].thumb,
                        "absolute top-1/2 -translate-y-1/2 left-0.5",
                        checked && sizes[size].translate
                    )}
                />
            </button>
            {label && (
                <span className="text-sm font-medium text-neutral-700">
                    {label}
                </span>
            )}
        </label>
    )
}

