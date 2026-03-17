import { Truck } from 'lucide-react'

interface SkeletonTableProps {
    rows?: number
}

// Shimmer efekti için skeleton component
function SkeletonCell({ width }: { width: string }) {
    return (
        <div
            className={`h-3 bg-border rounded animate-pulse ${width}`}
        />
    )
}

export function SkeletonTable({ rows = 5 }: SkeletonTableProps) {
    return (
        <>
            <div className="overflow-hidden rounded-xl border border-border bg-surface shadow-sm">
                <table className="w-full">
                    <thead>
                        <tr className="bg-bg-elevated border-b border-border">
                            <th className="px-4 py-4 text-left text-xs font-bold text-secondary uppercase tracking-wider w-[180px]">Araç</th>
                            <th className="px-4 py-4 text-left text-xs font-bold text-secondary uppercase tracking-wider w-[130px]">Plaka</th>
                            <th className="px-4 py-4 text-center text-xs font-bold text-secondary uppercase tracking-wider w-[70px]">Yıl</th>
                            <th className="px-4 py-4 text-right text-xs font-bold text-secondary uppercase tracking-wider w-[90px]">Tank</th>
                            <th className="px-4 py-4 text-right text-xs font-bold text-secondary uppercase tracking-wider w-[100px]">Hedef</th>
                            <th className="px-4 py-4 text-center text-xs font-bold text-secondary uppercase tracking-wider w-[90px]">Durum</th>
                            <th className="px-4 py-4 text-center text-xs font-bold text-secondary uppercase tracking-wider w-[70px]">İşlemler</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {Array.from({ length: rows }).map((_, index) => (
                            <tr
                                key={index}
                                className="animate-pulse"
                                style={{ animationDelay: `${index * 50}ms` }}
                            >
                                {/* Araç */}
                                <td className="px-4 py-3">
                                    <div className="flex items-center gap-2">
                                        <div className="w-9 h-9 rounded-lg bg-border flex items-center justify-center shrink-0">
                                            <Truck className="w-4 h-4 text-secondary" />
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
                                    <div className="w-14 h-5 bg-border rounded-full animate-pulse mx-auto" />
                                </td>
                                {/* İşlemler */}
                                <td className="px-4 py-3 text-center">
                                    <div className="w-7 h-7 bg-border rounded-lg animate-pulse mx-auto" />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </>
    )
}
