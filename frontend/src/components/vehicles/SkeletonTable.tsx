import { Truck } from 'lucide-react'

interface SkeletonTableProps {
    rows?: number
}

// Shimmer efekti için skeleton component
function SkeletonCell({ width }: { width: string }) {
    return (
        <div
            className={`h-3 bg-neutral-200 rounded animate-pulse ${width}`}
            style={{
                background: 'linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%)',
                backgroundSize: '200% 100%',
                animation: 'shimmer 1.5s infinite'
            }}
        />
    )
}

export function SkeletonTable({ rows = 5 }: SkeletonTableProps) {
    return (
        <>
            <style>{`
                @keyframes shimmer {
                    0% { background-position: 200% 0; }
                    100% { background-position: -200% 0; }
                }
            `}</style>
            <div className="overflow-hidden rounded-[24px] border border-neutral-200 bg-white shadow-sm">
                <table className="w-full">
                    <thead>
                        <tr className="bg-neutral-50 border-b border-neutral-100">
                            <th className="px-4 py-4 text-left text-xs font-bold text-neutral-500 uppercase tracking-wider w-[180px]">Araç</th>
                            <th className="px-4 py-4 text-left text-xs font-bold text-neutral-500 uppercase tracking-wider w-[130px]">Plaka</th>
                            <th className="px-4 py-4 text-center text-xs font-bold text-neutral-500 uppercase tracking-wider w-[70px]">Yıl</th>
                            <th className="px-4 py-4 text-right text-xs font-bold text-neutral-500 uppercase tracking-wider w-[90px]">Tank</th>
                            <th className="px-4 py-4 text-right text-xs font-bold text-neutral-500 uppercase tracking-wider w-[100px]">Hedef</th>
                            <th className="px-4 py-4 text-center text-xs font-bold text-neutral-500 uppercase tracking-wider w-[90px]">Durum</th>
                            <th className="px-4 py-4 text-center text-xs font-bold text-neutral-500 uppercase tracking-wider w-[70px]">İşlemler</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-100">
                        {Array.from({ length: rows }).map((_, index) => (
                            <tr
                                key={index}
                                className="animate-pulse"
                                style={{ animationDelay: `${index * 50}ms` }}
                            >
                                {/* Araç */}
                                <td className="px-4 py-3">
                                    <div className="flex items-center gap-2">
                                        <div className="w-9 h-9 rounded-lg bg-neutral-200 flex items-center justify-center shrink-0">
                                            <Truck className="w-4 h-4 text-neutral-300" />
                                        </div>
                                        <div className="space-y-1.5">
                                            <SkeletonCell width="w-16" />
                                            <SkeletonCell width="w-12" />
                                        </div>
                                    </div>
                                </td>
                                {/* Plaka */}
                                <td className="px-4 py-3">
                                    <SkeletonCell width="w-20" />
                                </td>
                                {/* Yıl */}
                                <td className="px-4 py-3 text-center">
                                    <SkeletonCell width="w-10 mx-auto" />
                                </td>
                                {/* Tank */}
                                <td className="px-4 py-3">
                                    <SkeletonCell width="w-12 ml-auto" />
                                </td>
                                {/* Hedef */}
                                <td className="px-4 py-3">
                                    <SkeletonCell width="w-14 ml-auto" />
                                </td>
                                {/* Durum */}
                                <td className="px-4 py-3 text-center">
                                    <div className="w-14 h-5 bg-neutral-200 rounded-full animate-pulse mx-auto" />
                                </td>
                                {/* İşlemler */}
                                <td className="px-4 py-3 text-center">
                                    <div className="w-7 h-7 bg-neutral-200 rounded-lg animate-pulse mx-auto" />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </>
    )
}
