import React, { useState } from 'react';
import UploadInvoice from './components/UploadInvoice';
import Dashboard from './components/Dashboard';
import Chatbot from './components/Chatbot';
import './styles/main.css';
import { Bot, FileText, LayoutDashboard, Sparkles } from 'lucide-react';

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleUploadSuccess = () => {
    // Increment trigger to force Dashboard to re-fetch data
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="app-container fade-in">
      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-center mb-12 gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-indigo-600 rounded-2xl shadow-lg shadow-indigo-500/20">
            <FileText className="text-white" size={32} />
          </div>
          <div>
            <h1 className="text-3xl font-black tracking-tight mb-0">AI <span className="text-indigo-400">Invoice_Automation</span></h1>
            <p className="text-sm text-gray-400 flex items-center gap-1">
              <Sparkles size={14} className="text-amber-400" /> AI-Powered Expense Automation
            </p>
          </div>
        </div>
        
        <nav className="flex gap-6 text-sm font-medium text-gray-400">
          <a href="#" className="text-indigo-400 hover:text-white transition-colors flex items-center gap-2">
            <LayoutDashboard size={18} /> Dashboard
          </a>
          <a href="#" className="hover:text-white transition-colors flex items-center gap-2">
            <Bot size={18} /> Documentation
          </a>
        </nav>
      </header>

      <main className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Sidebar / Upload Section */}
        <section className="md:col-span-1 space-y-6">
          <UploadInvoice onUploadSuccess={handleUploadSuccess} />
          
          <div className="glass-card bg-indigo-600/10 border-indigo-500/20">
            <h3 className="text-sm font-bold text-indigo-300 uppercase tracking-wider mb-2">Pro Tip</h3>
            <p className="text-xs text-gray-300 leading-relaxed">
              Upload consistently labeled PDF invoices for the best extraction accuracy. Our AI learns your patterns over time!
            </p>
          </div>
        </section>

        {/* Main Content / Dashboard Section */}
        <section className="md:col-span-2">
          <Dashboard refreshTrigger={refreshTrigger} />
        </section>
      </main>

      <footer className="mt-20 py-8 border-t border-white/5 text-center">
        <p className="text-gray-500 text-xs">
          &copy; 2026 AI Invoice-Automation. Built with React, Flask & MongoDB.
        </p>
      </footer>

      {/* Floating Chatbot */}
      <Chatbot />
    </div>
  );
}

export default App;
