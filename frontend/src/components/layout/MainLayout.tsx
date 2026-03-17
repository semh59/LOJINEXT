import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { useLocation } from 'react-router-dom'
import ErrorBoundary from '../common/ErrorBoundary'
import { ChatAssistant } from '../ai/ChatAssistant'

interface MainLayoutProps {
    children: React.ReactNode
    title?: string
    breadcrumb?: string
    hideChatAssistant?: boolean
}

export function MainLayout({ children, title, breadcrumb, hideChatAssistant }: MainLayoutProps) {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false)
    const location = useLocation()

    // LojiNext v2.0 Layout Rules:
    // Background: bg-base
    // Max Content Width: 1280px
    // Transitions: opacity 0 -> 1, y: 6px -> 0px in 220ms
    return (
        <div className="flex h-screen overflow-hidden font-sans text-primary bg-bg-base">
            <Sidebar
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
            />

            <div className="flex-1 flex flex-col min-w-0 relative h-full">
                <Header
                    onMenuClick={() => setIsSidebarOpen(true)}
                    title={title}
                    breadcrumb={breadcrumb}
                />

                <main className="flex-1 overflow-y-auto px-[24px] py-[32px] lg:px-[40px] custom-scrollbar focus:outline-none w-full relative">
                    <ErrorBoundary>
                        <div className="mx-auto w-full max-w-[1280px]">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={location.pathname}
                                    initial={{ opacity: 0, y: 6 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -6 }}
                                    transition={{ duration: 0.22, ease: "easeOut" }}
                                >
                                    {children}
                                </motion.div>
                            </AnimatePresence>
                        </div>
                    </ErrorBoundary>
                </main>
            </div>
            {!hideChatAssistant && <ChatAssistant />}
        </div>
    )
}
