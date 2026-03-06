import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSearchParams } from 'react-router-dom'
import { PremiumLayout } from '../components/layout/PremiumLayout'
import { VehiclesModule } from '../components/modules/VehiclesModule'
import { DriversModule } from '../components/modules/DriversModule'
import { TrailersModule } from '../components/modules/TrailersModule'
import { FleetInsights } from '../components/fleet/FleetInsights'
import { Truck, Users, Container } from 'lucide-react'
import { cn } from '../lib/utils'

type TabType = 'vehicles' | 'drivers' | 'trailers'

export default function FleetPage() {
    const [searchParams, setSearchParams] = useSearchParams()
    const [activeTab, setActiveTab] = useState<TabType>('vehicles')

    // Sync tab with URL
    useEffect(() => {
        const tab = searchParams.get('tab')
        if (tab === 'drivers') {
            setActiveTab('drivers')
        } else if (tab === 'trailers') {
            setActiveTab('trailers')
        } else {
            setActiveTab('vehicles')
        }
    }, [searchParams])

    const handleTabChange = (tab: TabType) => {
        setActiveTab(tab)
        setSearchParams({ tab })
    }

    return (
        <PremiumLayout title="Filo Yönetimi" primaryColor="#d006f9">
            <div className="flex-1 w-full h-full p-6 animate-stagger-fade overflow-y-auto custom-scrollbar">
                {/* Fleet Insights Dashboard */}
                <FleetInsights activeTab={activeTab} />

                {/* Header & Tabs */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-6">
                    <div className="flex p-1.5 bg-[#1a0121]/60 backdrop-blur-md rounded-2xl w-fit overflow-x-auto border border-[#d006f9]/20 shadow-[0_0_15px_rgba(208,6,249,0.1)]">
                        <button
                            onClick={() => handleTabChange('vehicles')}
                            className={cn(
                                "flex items-center gap-3 px-6 py-2.5 rounded-xl text-sm font-bold uppercase transition-all whitespace-nowrap",
                                activeTab === 'vehicles'
                                    ? "bg-[#d006f9] text-white shadow-[0_0_15px_rgba(208,6,249,0.4)]"
                                    : "text-[#d006f9]/60 hover:text-[#d006f9] hover:bg-[#d006f9]/10"
                            )}
                        >
                            <Truck className="w-4 h-4" />
                            Araçlar
                        </button>
                        <button
                            onClick={() => handleTabChange('drivers')}
                            className={cn(
                                "flex items-center gap-3 px-6 py-2.5 rounded-xl text-sm font-bold uppercase transition-all whitespace-nowrap",
                                activeTab === 'drivers'
                                    ? "bg-[#d006f9] text-white shadow-[0_0_15px_rgba(208,6,249,0.4)]"
                                    : "text-[#d006f9]/60 hover:text-[#d006f9] hover:bg-[#d006f9]/10"
                            )}
                        >
                            <Users className="w-4 h-4" />
                            Sürücüler
                        </button>
                        <button
                            onClick={() => handleTabChange('trailers')}
                            className={cn(
                                "flex items-center gap-3 px-6 py-2.5 rounded-xl text-sm font-bold uppercase transition-all whitespace-nowrap",
                                activeTab === 'trailers'
                                    ? "bg-[#d006f9] text-white shadow-[0_0_15px_rgba(208,6,249,0.4)]"
                                    : "text-[#d006f9]/60 hover:text-[#d006f9] hover:bg-[#d006f9]/10"
                            )}
                        >
                            <Container className="w-4 h-4" />
                            Dorseler
                        </button>
                    </div>

                    {/* Right Side Stats */}
                    {/* ... (rest of stats) */}
                </div>

                {/* Content with Animation */}
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeTab}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                    >
                        {activeTab === 'vehicles' ? (
                            <VehiclesModule />
                        ) : activeTab === 'drivers' ? (
                            <DriversModule />
                        ) : (
                            <TrailersModule />
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
        </PremiumLayout>
    )
}
