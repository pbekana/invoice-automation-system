import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, X, Bot, Sparkles, Loader2 } from 'lucide-react';
import { sendMessage } from '../services/api';
import useAuthStore from '../store/useAuthStore';
import { AnimatePresence, motion } from 'framer-motion';

const Chatbot = () => {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  const user = useAuthStore(state => state.user);
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { 
      role: 'bot', 
      content: "Hello! I am your AI financial assistant. Ask me about invoice statuses, approval queues, outstanding balances, or vendor spend." 
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  if (!isAuthenticated) return null;

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsTyping(true);

    try {
      const data = await sendMessage(userMsg);
      setMessages(prev => [...prev, { role: 'bot', content: data.response || "No response received." }]);
    } catch {
      setMessages(prev => [...prev, { 
        role: 'bot', 
        content: "I could not retrieve live data at this moment. Ensure the backend server is reachable." 
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const formatMessage = (content) => {
    if (!content) return null;
    const parts = content.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-bold text-neutral-900 dark:text-white">{part.slice(2, -2)}</strong>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <>
      {/* Floating Action Button */}
      <div 
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-12 h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-full flex items-center justify-center shadow-lg shadow-blue-500/25 cursor-pointer z-30 transition-transform hover:scale-105 active:scale-95 border border-blue-400/30"
        title="Open AI Assistant"
        aria-label="Toggle AI Financial Assistant"
      >
        {isOpen ? <X size={20} /> : <MessageSquare size={20} />}
      </div>

      {/* Floating Chat Modal */}
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 15 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 15 }}
            transition={{ duration: 0.15 }}
            className="fixed bottom-20 right-4 sm:right-6 w-[360px] max-w-[calc(100vw-32px)] h-[480px] max-h-[calc(100vh-100px)] bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl shadow-2xl z-40 flex flex-col justify-between overflow-hidden"
          >
            {/* Header */}
            <div className="px-4 py-3 bg-neutral-50 dark:bg-neutral-950 border-b border-neutral-200 dark:border-neutral-800 flex justify-between items-center shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 rounded-lg flex items-center justify-center border border-blue-200 dark:border-blue-900/40">
                  <Bot size={16} />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-neutral-800 dark:text-neutral-100 flex items-center gap-1.5">
                    <span>Invoice Assistant</span>
                    <span className="text-[9px] bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300 font-bold px-1 py-0.5 rounded">
                      Live
                    </span>
                  </h3>
                  <p className="text-[10px] text-neutral-400">
                    Role: {user?.roles?.[0] || 'member'} • Real Database
                  </p>
                </div>
              </div>
              <button 
                onClick={() => setIsOpen(false)}
                className="p-1 rounded-md text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-colors"
                aria-label="Close Assistant"
              >
                <X size={16} />
              </button>
            </div>

            {/* Conversation Log */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3.5" ref={scrollRef}>
              {messages.map((m, i) => (
                <div 
                  key={i} 
                  className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex items-start gap-2 max-w-[85%] ${m.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold ${
                      m.role === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-neutral-200 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300'
                    }`}>
                      {m.role === 'user' ? 'U' : <Sparkles size={11} className="text-blue-500" />}
                    </div>

                    <div className={`p-2.5 rounded-2xl text-xs leading-relaxed ${
                      m.role === 'user'
                        ? 'bg-blue-600 text-white rounded-tr-none'
                        : 'bg-neutral-100 dark:bg-neutral-800/80 text-neutral-800 dark:text-neutral-200 border border-neutral-200/50 dark:border-neutral-700/50 rounded-tl-none whitespace-pre-wrap'
                    }`}>
                      {m.role === 'user' ? m.content : formatMessage(m.content)}
                    </div>
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-2 p-2 text-xs text-neutral-400">
                    <Loader2 size={13} className="animate-spin text-blue-500" />
                    <span>Querying verified records...</span>
                  </div>
                </div>
              )}
            </div>

            {/* Input Bar */}
            <form onSubmit={handleSend} className="p-2.5 bg-neutral-50 dark:bg-neutral-950 border-t border-neutral-200 dark:border-neutral-800 flex gap-2 shrink-0">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about bills, status, or vendors..."
                className="input-field text-xs py-1.5 flex-1"
                disabled={isTyping}
              />
              <button 
                type="submit" 
                disabled={isTyping || !input.trim()}
                className="btn-primary p-2 shrink-0 rounded-lg flex items-center justify-center"
                aria-label="Send query"
              >
                <Send size={14} />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default Chatbot;
