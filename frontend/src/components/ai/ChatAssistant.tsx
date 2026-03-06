import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, X, Send, Bot, Loader2, Maximize2, Minimize2, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { aiApi, ChatMessage } from '../../services/api/ai-service';
import { cn } from '../../lib/utils';
import { useAiStore } from '../../stores/use-ai-store';

export const ChatAssistant: React.FC = () => {
    const { 
        isOpen, toggleOpen, 
        isExpanded, toggleExpanded,
        messages, addMessage, 
        clearHistory,
        status, checkStatus 
    } = useAiStore();
    
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Initial status check
    useEffect(() => {
        const interval = setInterval(() => {
            if (isOpen && status !== 'ready') {
                checkStatus();
            }
        }, 5000);

        if (isOpen) {
             checkStatus();
        }

        return () => clearInterval(interval);
    }, [isOpen, status, checkStatus]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        if (isOpen) {
            scrollToBottom();
        }
    }, [messages, isOpen]);

    const handleSendMessage = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: ChatMessage = { role: 'user', content: input };
        addMessage(userMessage);
        setInput('');
        setIsLoading(true);

        try {
            const response = await aiApi.chat({
                message: input,
                history: messages
            });

            const assistantMessage: ChatMessage = { 
                role: 'assistant', 
                content: response.response 
            };
            addMessage(assistantMessage);
        } catch (error) {
            console.error('AI Chat Error:', error);
            toast.error('AI yanıt veremedi. Lütfen bağlantınızı kontrol edin.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed bottom-24 right-6 z-[9999]">
            {/* Toggle Button */}
            {!isOpen && (
                <motion.button
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={toggleOpen}
                    className="w-16 h-16 rounded-full bg-[#22d3ee] text-[#050b0e] shadow-[0_0_30px_rgba(34,211,238,0.5)] flex items-center justify-center group relative overflow-hidden ring-4 ring-[#050b0e]"
                >
                    <div className="absolute inset-0 bg-gradient-to-tr from-white/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <Sparkles className="w-8 h-8 relative z-10" />
                </motion.button>
            )}

            {/* Chat Window */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.8, y: 100, transformOrigin: 'bottom right' }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.8, y: 100 }}
                        className={cn(
                            "glass-panel shadow-[0_0_80px_rgba(34,211,238,0.1)] rounded-[32px] border border-[#22d3ee]/20 flex flex-col overflow-hidden transition-all duration-300",
                            isExpanded ? "w-[800px] h-[85vh] max-h-[1000px]" : "w-[420px] h-[650px]"
                        )}
                    >
                        {/* Header */}
                        <div className="p-6 bg-black/40 border-b border-white/5 flex items-center justify-between shrink-0">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-[#22d3ee]/20 flex items-center justify-center border border-[#22d3ee]/40 shadow-[0_0_15px_rgba(34,211,238,0.3)]">
                                    <Sparkles className="w-5 h-5 text-[#22d3ee]" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-lg leading-none tracking-tight text-white mb-1.5">LojiNext AI Asistan</h3>
                                    <div className="flex items-center gap-1.5">
                                        {status === 'ready' && (
                                            <>
                                                <span className="w-1.5 h-1.5 rounded-full bg-[#0df259] shadow-[0_0_5px_#0df259] animate-pulse" />
                                                <span className="text-[10px] font-bold text-[#0df259] uppercase tracking-widest">Hazır</span>
                                            </>
                                        )}
                                        {status === 'loading' && (
                                            <>
                                                <span className="w-1.5 h-1.5 rounded-full bg-[#f2a20d] shadow-[0_0_5px_#f2a20d] animate-pulse" />
                                                <span className="text-[10px] font-bold text-[#f2a20d] uppercase tracking-widest">Hazırlanıyor...</span>
                                            </>
                                        )}
                                        {status === 'error' && (
                                            <>
                                                <span className="w-1.5 h-1.5 rounded-full bg-red-500 shadow-[0_0_5px_#ef4444]" />
                                                <span className="text-[10px] font-bold text-red-500 uppercase tracking-widest">Hata</span>
                                            </>
                                        )}
                                        {status === 'offline' && (
                                            <>
                                                <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Bağlanıyor...</span>
                                            </>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={clearHistory}
                                    className="p-2.5 hover:bg-white/10 rounded-xl transition-colors text-white/50 hover:text-red-400"
                                    title="Sohbeti Temizle"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                                <button 
                                    onClick={toggleExpanded}
                                    className="p-2.5 hover:bg-white/10 rounded-xl transition-colors text-white/50 hover:text-white"
                                >
                                    {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                                </button>
                                <button 
                                    onClick={toggleOpen}
                                    className="p-2.5 hover:bg-white/10 rounded-xl transition-colors text-white/50 hover:text-white"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                        </div>

                        {/* Suggestion Chips */}
                        {messages.length === 0 && (
                            <div className="px-6 py-4 flex gap-2 overflow-x-auto custom-scrollbar border-b border-white/5">
                                <button onClick={() => setInput('Tüm filonun sağlık durumu nedir?')} className="bg-[#22d3ee]/10 border border-[#22d3ee]/20 px-4 py-2 rounded-xl text-[11px] font-bold whitespace-nowrap text-[#22d3ee] hover:bg-[#22d3ee]/20 transition-all uppercase tracking-tight">Tüm filonun sağlık durumu nedir?</button>
                                <button onClick={() => setInput('En verimli güzergah hangisi?')} className="bg-[#22d3ee]/10 border border-[#22d3ee]/20 px-4 py-2 rounded-xl text-[11px] font-bold whitespace-nowrap text-[#22d3ee] hover:bg-[#22d3ee]/20 transition-all uppercase tracking-tight">En verimli güzergah hangisi?</button>
                                <button onClick={() => setInput('Bakım zamanı yaklaşanlar kimler?')} className="bg-[#22d3ee]/10 border border-[#22d3ee]/20 px-4 py-2 rounded-xl text-[11px] font-bold whitespace-nowrap text-[#22d3ee] hover:bg-[#22d3ee]/20 transition-all uppercase tracking-tight">Bakım zamanı yaklaşanlar</button>
                            </div>
                        )}

                        {/* Messages Area */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-transparent">
                            {messages.map((msg: ChatMessage, idx: number) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={cn(
                                        "flex flex-col gap-2",
                                        msg.role === 'user' ? "items-end" : "items-start"
                                    )}
                                >
                                    <div className={cn(
                                        "px-5 py-4 text-sm max-w-[85%] shadow-xl rounded-[24px]",
                                        msg.role === 'user' 
                                            ? "bg-[#22d3ee] text-[#050b0e] rounded-tr-sm font-bold shadow-[0_0_20px_rgba(34,211,238,0.2)]" 
                                            : "bg-white/5 text-slate-100 rounded-tl-sm border border-white/10 leading-relaxed backdrop-blur-md"
                                    )}>
                                        {msg.role === 'assistant' && (
                                            <div className="flex items-center gap-2 text-[#22d3ee] mb-3">
                                                <Bot className="w-4 h-4" />
                                                <span className="text-[10px] font-black uppercase tracking-widest">LojiNext AI</span>
                                            </div>
                                        )}
                                        {msg.content}
                                    </div>
                                </motion.div>
                            ))}
                            {isLoading && (
                                <div className="flex flex-col items-start gap-2 max-w-[85%]">
                                    <div className="bg-white/5 text-[#22d3ee] px-5 py-4 rounded-2xl rounded-tl-none border border-white/10 flex items-center gap-3 backdrop-blur-md">
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        <span className="text-[10px] font-black uppercase tracking-widest">Düşünüyor...</span>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                         {/* Input Area */}
                        <form 
                            onSubmit={handleSendMessage}
                            className="p-5 bg-black/60 border-t border-white/5 flex items-center gap-3 shrink-0"
                        >
                            <div className="flex-1 relative">
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="LojiNext Asistan'a sor..."
                                    className="w-full bg-black/40 border border-white/10 rounded-2xl pl-5 pr-12 py-3.5 text-sm text-white placeholder-white/20 focus:outline-none focus:border-[#22d3ee]/50 focus:ring-1 focus:ring-[#22d3ee]/30 transition-all shadow-inner"
                                    disabled={isLoading}
                                />
                                <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-50">
                                    <Sparkles className="w-4 h-4 text-[#22d3ee]" />
                                </div>
                            </div>
                            <button
                                type="submit"
                                disabled={!input.trim() || isLoading}
                                className="w-[52px] h-[52px] rounded-2xl bg-[#22d3ee] text-[#050b0e] flex items-center justify-center shadow-[0_0_20px_rgba(34,211,238,0.4)] hover:scale-105 active:scale-95 disabled:opacity-50 disabled:scale-100 transition-all shrink-0"
                            >
                                <Send className="w-5 h-5 ml-1" />
                            </button>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

