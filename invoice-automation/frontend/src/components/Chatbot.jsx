import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, X, Bot, User, Loader2 } from 'lucide-react';
import { sendMessage } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'bot', content: 'Hi! I\'m your AI expense assistant. Ask me anything about your spending!' }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

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
      setMessages(prev => [...prev, { role: 'bot', content: "Sorry, I'm having trouble connecting to the server. Please try again later." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <>
      <div className="chatbot-bubble fade-in" onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? <X color="white" /> : <MessageSquare color="white" />}
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            className="chat-window glass-card"
          >
            <div className="p-4 border-bottom border-white/10 bg-indigo-600/20 flex justify-between items-center rounded-t-xl">
              <h3 className="text-sm font-bold flex items-center gap-2 m-0 !bg-none" style={{ webkitTextFillColor: 'white' }}>
                <Bot size={18} className="text-indigo-400" /> Expense Assistant
              </h3>
              <X size={18} className="text-gray-400 cursor-pointer" onClick={() => setIsOpen(false)} />
            </div>

            <div className="chat-messages" ref={scrollRef}>
              {messages.map((m, i) => (
                <div key={i} className={`message ${m.role === 'user' ? 'message-user' : 'message-bot'}`}>
                  <div className="flex items-start gap-2">
                    {m.role === 'bot' && <Bot size={14} className="mt-1 text-indigo-300" />}
                    <span className="whitespace-pre-wrap">{m.content}</span>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="message message-bot">
                  <div className="flex items-center gap-2">
                    <Loader2 size={14} className="animate-spin text-indigo-400" />
                    <span className="italic text-xs text-gray-400">AI is thinking...</span>
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={handleSend} className="p-4 border-t border-white/10 flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about your expenses..."
                className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
              />
              <button type="submit" className="bg-indigo-600 p-2 rounded-lg hover:bg-indigo-500 transition-colors">
                <Send size={18} color="white" />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default Chatbot;
