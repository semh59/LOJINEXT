import * as React from "react"
import { useState, useRef, useEffect } from "react"
import { MoreVertical } from "lucide-react"
import { cn } from "../../lib/utils"

export interface DropdownMenuItem {
    label: string
    icon?: React.ReactNode
    onClick: () => void
    variant?: 'default' | 'danger'
    disabled?: boolean
}

export interface DropdownMenuProps {
    items: DropdownMenuItem[]
    trigger?: React.ReactNode
    align?: 'left' | 'right'
    className?: string
}

export function DropdownMenu({
    items,
    trigger,
    align = 'right',
    className
}: DropdownMenuProps) {
    const [isOpen, setIsOpen] = useState(false)
    const menuRef = useRef<HTMLDivElement>(null)
    const buttonRef = useRef<HTMLButtonElement>(null)

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsOpen(false)
            }
        }

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside)
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside)
        }
    }, [isOpen])

    useEffect(() => {
        const handleEscape = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                setIsOpen(false)
                buttonRef.current?.focus()
            }
        }

        if (isOpen) {
            document.addEventListener('keydown', handleEscape)
        }

        return () => {
            document.removeEventListener('keydown', handleEscape)
        }
    }, [isOpen])

    const handleItemClick = (item: DropdownMenuItem) => {
        if (!item.disabled) {
            item.onClick()
            setIsOpen(false)
        }
    }

    const renderTrigger = () => {
        if (!trigger) {
            return (
                <button
                    ref={buttonRef}
                    type="button"
                    onClick={() => setIsOpen(!isOpen)}
                    className="p-[8px] text-secondary hover:text-primary hover:bg-bg-elevated rounded-[6px] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/5"
                    aria-haspopup="true"
                    aria-expanded={isOpen}
                >
                    <MoreVertical className="w-[20px] h-[20px]" />
                </button>
            )
        }

        if (React.isValidElement(trigger)) {
            return React.cloneElement(trigger as React.ReactElement<any>, {
                ref: buttonRef,
                onClick: (e: React.MouseEvent) => {
                    (trigger.props as any).onClick?.(e)
                    setIsOpen(!isOpen)
                },
                'aria-haspopup': "true",
                'aria-expanded': isOpen
            })
        }

        return (
            <div
                ref={buttonRef as any}
                onClick={() => setIsOpen(!isOpen)}
                className="cursor-pointer"
            >
                {trigger}
            </div>
        )
    }

    // LojiNext v2.0 Dropdown Rules: clip-path or max-height unfold, 180ms
    return (
        <div ref={menuRef} className={cn("relative inline-block", className)}>
            {renderTrigger()}

            <div
                className={cn(
                    "absolute z-50 mt-[4px] min-w-[180px] p-[6px] bg-surface rounded-[10px] shadow-premium border border-border",
                    // Unfold animation mimicking max-height/clip-path natively in tailwind
                    "origin-top transition-all duration-180 ease-out",
                    isOpen ? "opacity-100 scale-y-100 transform-none select-auto pointer-events-auto" : "opacity-0 scale-y-95 pointer-events-none",
                    align === 'right' ? "right-0" : "left-0"
                )}
                role="menu"
            >
                {items.map((item, index) => (
                    <button
                        key={index}
                        type="button"
                        role="menuitem"
                        disabled={item.disabled}
                        onClick={() => handleItemClick(item)}
                        className={cn(
                            "w-full flex items-center gap-[12px] px-[12px] py-[8px] text-[13px] font-medium transition-colors rounded-[6px] select-none outline-none",
                            item.variant === 'danger'
                                ? "text-danger hover:bg-danger/10 focus:bg-danger/10"
                                : "text-primary hover:bg-bg-elevated focus:bg-bg-elevated",
                            item.disabled && "opacity-50 cursor-not-allowed"
                        )}
                    >
                        {item.icon && (
                            <span className="w-[16px] h-[16px] flex items-center justify-center shrink-0">
                                {item.icon}
                            </span>
                        )}
                        {item.label}
                    </button>
                ))}
            </div>
        </div>
    )
}
