import { useState, useCallback, useEffect, useRef } from 'react'

/**
 * localStorage'den widget sıralamasını okuyup yazan hook.
 * Drag & drop ile widget'ların sıralaması değiştirilebilir.
 * 
 * @param defaultOrder Varsayılan widget ID sıralaması
 * @param storageKey localStorage key
 */
export function useWidgetLayout(
    defaultOrder: string[],
    storageKey = 'dashboard_order'
) {
    const [order, setOrder] = useState<string[]>(() => {
        try {
            const saved = localStorage.getItem(storageKey)
            if (saved) {
                const parsed: string[] = JSON.parse(saved)
                // If the saved order is different than the default, merge them
                // This ensures new widgets (like ai-prediction) show up even if order was saved
                const missing = defaultOrder.filter(id => !parsed.includes(id))
                if (missing.length > 0) {
                    return [...parsed, ...missing]
                }
                return parsed
            }
        } catch {
            // Corrupted localStorage, fall back
        }
        return defaultOrder
    })

    // Persist to localStorage
    useEffect(() => {
        localStorage.setItem(storageKey, JSON.stringify(order))
    }, [order, storageKey])

    // Drag state
    const dragItemRef = useRef<number | null>(null)
    const dragOverRef = useRef<number | null>(null)

    const handleDragStart = useCallback((index: number) => {
        dragItemRef.current = index
    }, [])

    const handleDragEnter = useCallback((index: number) => {
        dragOverRef.current = index
    }, [])

    const handleDragEnd = useCallback(() => {
        const from = dragItemRef.current
        const to = dragOverRef.current
        if (from === null || to === null || from === to) {
            dragItemRef.current = null
            dragOverRef.current = null
            return
        }

        setOrder((prev) => {
            const next = [...prev]
            const [removed] = next.splice(from, 1)
            next.splice(to, 0, removed)
            return next
        })

        dragItemRef.current = null
        dragOverRef.current = null
    }, [])

    const resetOrder = useCallback(() => {
        setOrder(defaultOrder)
        localStorage.removeItem(storageKey)
    }, [defaultOrder, storageKey])

    return {
        order,
        handleDragStart,
        handleDragEnter,
        handleDragEnd,
        resetOrder,
    }
}
