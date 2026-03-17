import React from 'react';
import { ArrowLeftRight, Weight } from 'lucide-react';
import { cn } from '../../../lib/utils';

interface RoundTripSelectorProps {
    returnType: 'none' | 'empty' | 'loaded';
    setReturnType: (type: 'none' | 'empty' | 'loaded') => void;
    isReadOnly?: boolean;
}

export const RoundTripSelector: React.FC<RoundTripSelectorProps> = React.memo(({
    returnType,
    setReturnType,
    isReadOnly = false
}) => {
    return (
        <div className="bg-base p-2.5 rounded-[20px] flex flex-wrap md:flex-nowrap items-center border border-border shadow-inner gap-3">
            <button
                type="button"
                disabled={isReadOnly}
                onClick={() => setReturnType('none')}
                className={cn(
                    "flex-1 min-w-[100px] flex items-center justify-center gap-2 py-4 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200 border-2",
                    returnType === 'none' 
                        ? "bg-text-secondary text-bg-base border-text-secondary shadow-sm" 
                        : "bg-surface text-secondary border-transparent hover:border-border hover:text-primary"
                )}
            >
                <ArrowLeftRight className="w-5 h-5" />
                TEK YÖN
            </button>
            <button
                type="button"
                disabled={isReadOnly}
                onClick={() => setReturnType('empty')}
                className={cn(
                    "flex-1 min-w-[100px] flex items-center justify-center gap-2 py-4 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200 border-2",
                    returnType === 'empty'
                        ? "bg-accent text-bg-base border-accent shadow-accent/20" 
                        : "bg-surface text-secondary border-transparent hover:border-border hover:text-primary"
                )}
            >
                <ArrowLeftRight className="w-5 h-5" />
                BOŞ DÖNÜŞ
            </button>
            <button
                type="button"
                disabled={isReadOnly}
                onClick={() => setReturnType('loaded')}
                className={cn(
                    "flex-1 min-w-[100px] flex items-center justify-center gap-2 py-4 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200 border-2",
                    returnType === 'loaded'
                        ? "bg-warning text-bg-base border-warning shadow-warning/20" 
                        : "bg-surface text-secondary border-transparent hover:border-border hover:text-primary"
                )}
            >
                <Weight className="w-5 h-5" />
                DOLU DÖNÜŞ
            </button>
        </div>
    );
});
