import { motion, AnimatePresence } from 'framer-motion'
import { useUrlState } from '../hooks/use-url-state'
import { PremiumLayout } from '../components/layout/PremiumLayout'
import { VehiclesModule } from '../components/modules/VehiclesModule'
import { DriversModule } from '../components/modules/DriversModule'
import { TrailersModule } from '../components/modules/TrailersModule'
import { FleetInsights } from '../components/fleet/FleetInsights'
import { Truck, Users, Container } from 'lucide-react'
import { cn } from '../lib/utils'

type TabType = 'vehicles' | 'drivers' | 'trailers'

export default function FleetPage() {
    const [{ tab: activeTab }, setUrlState] = useUrlState({
        tab: 'vehicles' as TabType,
        page: undefined as number | undefined,
        search: undefined as string | undefined,
        marka: undefined as string | undefined,
        model: undefined as string | undefined,
        min_yil: undefined as string | undefined,
        max_yil: undefined as string | undefined,
        aktif: undefined as boolean | undefined,
        ehliyet: undefined as string | undefined,
        view: undefined as string | undefined
    })

    const handleTabChange = (tab: TabType) => {
        // Clear sub-module specific params when switching tabs to prevent state leaks (e.g., page 5 of vehicles vs page 1 of drivers)
        setUrlState({ 
            tab,
            page: undefined,
            search: undefined,
            marka: undefined,
            model: undefined,
            min_yil: undefined,
            max_yil: undefined,
            aktif: undefined,
            ehliyet: undefined,
            view: undefined
        })
    }

    return (
        <PremiumLayout title="Filo Yönetimi">
            <div className="flex-1 w-full h-full px-6 py-8 animate-stagger-fade overflow-y-auto custom-scrollbar bg-transparent">
                {/* Fleet Insights Dashboard */}
                <FleetInsights activeTab={activeTab} />

                {/* Header & Tabs */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-6">
                    <div className="flex p-1 bg-surface border border-border rounded-[10px] w-fit overflow-x-auto shadow-sm relative">
                        {/* Selected background indicator */}
                        
                        <button
                            onClick={() => handleTabChange('vehicles')}
                            className={cn(
                                "relative flex items-center justify-center gap-2 px-6 py-2 rounded-[8px] text-[13px] font-bold uppercase transition-colors whitespace-nowrap tracking-tight z-10",
                                activeTab === 'vehicles' ? "text-accent" : "text-secondary hover:text-primary"
                            )}
                        >
                            {activeTab === 'vehicles' && (
                                <motion.div
                                    layoutId="fleetTabIndicator"
                                    className="absolute inset-0 bg-accent/10 border border-accent/20 rounded-[8px] -z-10"
                                    transition={{ type: "spring", bounce: 0.2, duration: 0.3 }}
                                />
                            )}
                            <Truck className="w-4 h-4" />
                            Araçlar
                        </button>

                        <button
                            onClick={() => handleTabChange('drivers')}
                            className={cn(
                                "relative flex items-center justify-center gap-2 px-6 py-2 rounded-[8px] text-[13px] font-bold uppercase transition-colors whitespace-nowrap tracking-tight z-10",
                                activeTab === 'drivers' ? "text-accent" : "text-secondary hover:text-primary"
                            )}
                        >
                            {activeTab === 'drivers' && (
                                <motion.div
                                    layoutId="fleetTabIndicator"
                                    className="absolute inset-0 bg-accent/10 border border-accent/20 rounded-[8px] -z-10"
                                    transition={{ type: "spring", bounce: 0.2, duration: 0.3 }}
                                />
                            )}
                            <Users className="w-4 h-4" />
                            Sürücüler
                        </button>

                        <button
                            onClick={() => handleTabChange('trailers')}
                            className={cn(
                                "relative flex items-center justify-center gap-2 px-6 py-2 rounded-[8px] text-[13px] font-bold uppercase transition-colors whitespace-nowrap tracking-tight z-10",
                                activeTab === 'trailers' ? "text-accent" : "text-secondary hover:text-primary"
                            )}
                        >
                            {activeTab === 'trailers' && (
                                <motion.div
                                    layoutId="fleetTabIndicator"
                                    className="absolute inset-0 bg-accent/10 border border-accent/20 rounded-[8px] -z-10"
                                    transition={{ type: "spring", bounce: 0.2, duration: 0.3 }}
                                />
                            )}
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
