import { useState } from 'react'
import { motion } from 'framer-motion'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
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

    return (
        <div className="flex h-screen overflow-hidden font-sans selection:bg-primary/20">
            <Sidebar
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
            />

            <div className="flex-1 flex flex-col min-w-0 relative">
                {/* Background Decorations */}
                <div className="absolute top-0 right-0 -z-0 w-[500px] h-[500px] bg-primary/5 rounded-full blur-3xl opacity-50 pointer-events-none" />
                <div className="absolute bottom-0 left-0 -z-0 w-[300px] h-[300px] bg-brand/5 rounded-full blur-3xl opacity-50 pointer-events-none" />

                <Header
                    onMenuClick={() => setIsSidebarOpen(true)}
                    title={title}
                    breadcrumb={breadcrumb}
                />

                <main className="flex-1 overflow-y-auto p-4 md:p-10 pb-32 custom-scrollbar focus:outline-none">
                    <ErrorBoundary>
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                            className="max-w-[1600px] mx-auto"
                        >
                            {children}
                        </motion.div>
                    </ErrorBoundary>
                </main>
            </div>
            {!hideChatAssistant && <ChatAssistant />}
        </div>
    )
}
