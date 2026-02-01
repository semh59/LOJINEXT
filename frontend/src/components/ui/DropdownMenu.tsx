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

    // Click dışına tıklandığında kapat
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

    // ESC tuşu ile kapat
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
                    className="p-2 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 rounded-lg transition-all"
                    aria-haspopup="true"
                    aria-expanded={isOpen}
                >
                    <MoreVertical className="w-4 h-4" />
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

    return (
        <div ref={menuRef} className={cn("relative inline-block", className)}>
            {renderTrigger()}

            {isOpen && (
                <div
                    className={cn(
                        "absolute z-50 mt-1 min-w-[160px] py-1 bg-white rounded-xl shadow-lg border border-neutral-100",
                        "animate-in fade-in-0 zoom-in-95 duration-100",
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
                                "w-full flex items-center gap-2 px-3 py-2 text-sm font-medium transition-colors",
                                item.variant === 'danger'
                                    ? "text-red-600 hover:bg-red-50"
                                    : "text-neutral-700 hover:bg-neutral-50",
                                item.disabled && "opacity-50 cursor-not-allowed"
                            )}
                        >
                            {item.icon && (
                                <span className="w-4 h-4 flex items-center justify-center">
                                    {item.icon}
                                </span>
                            )}
                            {item.label}
                        </button>
                    ))}
                </div>
            )}
        </div>
    )
}
