import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, X, Bot, User, Loader2, Sparkles } from 'lucide-react';
import { sendMessage } from '../services/api';
import useAuthStore from '../store/useAuthStore';
import { motion, AnimatePresence } from 'framer-motion';

const Chatbot = () => {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'bot', content: "Hi! I'm your AI financial assistant. Ask me questions about vendor spending, invoice categories, or outstanding customer balances." }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  // If user is not authenticated, do not show the chatbot at all
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
      setMessages(prev => [...prev, { role: 'bot', content: data.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'bot', content: "I'm having trouble retrieving company statistics. Make sure the backend server is running." }]);
    } finally {
      setIsTyping(false);
    }
  };

  const formatMessage = (content) => {
    if (!content) return null;
    const parts = content.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-extrabold text-slate-900 dark:text-white">{part.slice(2, -2)}</strong>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <>
      {/* Bubble launcher */}
      <div 
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full flex items-center justify-center shadow-lg shadow-blue-500/20 cursor-pointer z-50 transition-transform active:scale-95 border border-blue-500/30"
        title="AI Financial Assistant"
      >
        {isOpen ? <X size={24} /> : <MessageSquare size={24} />}
      </div>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed bottom-24 right-6 w-96 max-w-[calc(100vw-32px)] h-[500px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl z-50 flex flex-col justify-between overflow-hidden"
          >
            {/* Header */}
            <div className="p-4 bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-50 dark:bg-blue-950/30 text-blue-500 rounded-lg flex items-center justify-center border border-blue-100 dark:border-blue-900/30">
                  <Bot size={18} />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider flex items-center gap-1">
                    <span>FinAssistant</span>
                    <span className="text-[8px] bg-blue-105 text-blue-500 px-1 py-0.5 rounded">AI</span>
                  </h3>
                  <p className="text-[10px] text-slate-400 mt-0.5">Linked to company database</p>
                </div>
              </div>
              <button 
                onClick={() => setIsOpen(false)}
                className="p-1 rounded text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X size={16} />
              </button>
            </div>

            {/* Scroll Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
              {messages.map((m, i) => (
                <div 
                  key={i} 
                  className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex items-start gap-2.5 max-w-[85%] ${m.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    
                    {/* Icon indicator */}
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                      m.role === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                    }`}>
                      {m.role === 'user' ? 'U' : <Sparkles size={12} className="text-blue-500" />}
                    </div>

                    {/* Bubble */}
                    <div className={`p-3 rounded-2xl text-xs leading-relaxed ${
                      m.role === 'user'
                        ? 'bg-blue-600 text-white rounded-tr-none'
                        : 'bg-slate-50 dark:bg-slate-850 text-slate-700 dark:text-slate-300 border border-slate-100 dark:border-slate-800 rounded-tl-none'
                    }`}>
                      {m.role === 'user' ? m.content : formatMessage(m.content)}
                    </div>

                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="flex items-start gap-2.5 max-w-[85%]">
                    <div className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center shrink-0">
                      <Loader2 size={12} className="animate-spin text-blue-500" />
                    </div>
                    <div className="p-3 bg-slate-50 dark:bg-slate-850 text-slate-400 italic text-xs rounded-2xl rounded-tl-none border border-slate-100 dark:border-slate-800">
                      Calculating values...
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Input Form footer */}
            <form onSubmit={handleSend} className="p-3 bg-slate-55 border-t border-slate-200 dark:border-slate-800 flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask e.g. What is our total outstanding balance?"
                className="input-field text-xs py-1.5 flex-1"
                disabled={isTyping}
              />
              <button 
                type="submit" 
                disabled={isTyping}
                className="btn-primary p-2 shrink-0 rounded-lg flex items-center justify-center"
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
