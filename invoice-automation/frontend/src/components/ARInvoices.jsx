import React, { useState, useEffect } from 'react';
import { FileText, Plus, Search, Eye, Send, Check, X, Filter, DollarSign, Clock, CheckCircle2, ChevronRight, AlertCircle, RefreshCw } from 'lucide-react';
import { getARInvoices, sendARInvoice, markARInvoicePaid } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import useToastStore from '../store/useToastStore';

const StatusBadge = ({ status }) => {
  const styles = {
    draft: 'badge-saas-gray',
    sent: 'badge-saas-blue border-blue-200 dark:border-blue-900/30',
    paid: 'badge-saas-green border-green-200 dark:border-green-900/30',
    overdue: 'badge-saas-red border-red-200 dark:border-red-900/30',
    cancelled: 'badge-saas-gray',
  };

  return (
    <span className={`badge-saas border px-2.5 py-0.5 capitalize ${styles[status] || styles.draft}`}>
      {status || 'draft'}
    </span>
  );
};

export default function ARInvoices() {
  const navigate = useNavigate();
  const addToast = useToastStore(state => state.addToast);
  const [invoices, setInvoices] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [error, setError] = useState('');
  const [updatingId, setUpdatingId] = useState(null);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      const data = await getARInvoices(params);
      setInvoices(data.invoices || []);
      setTotalCount(data.total || 0);
    } catch (err) { 
      console.error(err);
      setError('Failed to fetch Accounts Receivable invoices from server.'); 
    } finally { 
      setLoading(false); 
    }
  };

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      load();
    }, 300);
    return () => clearTimeout(delayDebounce);
  }, [search, statusFilter]);

  const handleSend = async (id) => {
    if (!window.confirm('Are you sure you want to mark this invoice as sent?')) return;
    setUpdatingId(id);
    try { 
      await sendARInvoice(id);
      addToast('Invoice marked as sent.', 'success');
      load(); 
    } catch (err) { 
      addToast('Failed to update invoice status to sent.', 'error');
    } finally {
      setUpdatingId(null);
    }
  };

  const handlePaid = async (id) => {
    if (!window.confirm('Record payment for this invoice? Status will change to paid.')) return;
    setUpdatingId(id);
    try { 
      await markARInvoicePaid(id);
      addToast('Payment recorded. Invoice marked as paid.', 'success');
      load(); 
    } catch (err) { 
      addToast('Failed to record payment on the invoice.', 'error');
    } finally {
      setUpdatingId(null);
    }
  };

  // Aggregated KPIs
  const totalRevenue = invoices.filter(i => i.status === 'paid').reduce((s, i) => s + (i.total || i.grand_total || 0), 0);
  const outstanding = invoices.filter(i => i.status === 'sent').reduce((s, i) => s + (i.total || i.grand_total || 0), 0);
  const draftsCount = invoices.filter(i => i.status === 'draft').length;

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <FileText className="text-blue-500" /> Accounts Receivable
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Build, dispatch, and track client invoices & collected revenue
          </p>
        </div>
        <button
          onClick={() => navigate('/ar/invoices/new')}
          className="btn-primary py-2 text-xs flex items-center gap-1.5 shadow-md shadow-blue-500/10"
        >
          <Plus size={14} />
          <span>New Invoice Builder</span>
        </button>
      </div>

      {/* Mini KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        
        {/* Rev */}
        <div className="card-premium p-5 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-450 uppercase tracking-wider block">Collected Revenue</span>
            <span className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 font-mono block mt-1">
              ${totalRevenue.toFixed(2)}
            </span>
          </div>
          <div className="p-2.5 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-500 rounded-xl border border-emerald-100 dark:border-emerald-900/30">
            <CheckCircle2 size={20} />
          </div>
        </div>

        {/* Outstanding */}
        <div className="card-premium p-5 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-450 uppercase tracking-wider block">Outstanding Balance</span>
            <span className="text-2xl font-extrabold text-blue-600 dark:text-blue-400 font-mono block mt-1">
              ${outstanding.toFixed(2)}
            </span>
          </div>
          <div className="p-2.5 bg-blue-50 dark:bg-blue-950/20 text-blue-500 rounded-xl border border-blue-100 dark:border-blue-900/30">
            <Clock size={20} />
          </div>
        </div>

        {/* Drafts */}
        <div className="card-premium p-5 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-450 uppercase tracking-wider block">Draft Invoices</span>
            <span className="text-2xl font-extrabold text-slate-700 dark:text-slate-300 font-mono block mt-1">
              {draftsCount}
            </span>
          </div>
          <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-800 text-slate-500">
            <FileText size={20} />
          </div>
        </div>

      </div>

      {error && (
        <div className="bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/50 rounded-xl p-4 text-rose-800 dark:text-rose-200 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
          <button onClick={() => setError('')} className="p-1 rounded hover:bg-rose-100 dark:hover:bg-rose-950/40">
            <X size={14}/>
          </button>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            className="input-field pl-9 text-xs" 
            placeholder="Search customer, email, or invoice number..." 
            value={search} 
            onChange={e => setSearch(e.target.value)} 
          />
        </div>
        <div className="w-full sm:w-48 relative">
          <Filter size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          <select 
            className="input-field pl-9 pr-8 text-xs appearance-none cursor-pointer" 
            value={statusFilter} 
            onChange={e => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            {['draft', 'sent', 'paid', 'overdue', 'cancelled'].map(s => (
              <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
            ))}
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-400" />
        </div>
      </div>

      {/* Directory Table */}
      <div className="card-premium overflow-hidden bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
        {loading ? (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {[1, 2, 3].map((n) => (
              <div key={n} className="p-4 animate-pulse flex items-center justify-between">
                <div className="space-y-2 flex-1">
                  <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/4" />
                  <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-1/3" />
                </div>
                <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-16" />
                <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded w-20 ml-8" />
              </div>
            ))}
          </div>
        ) : invoices.length === 0 ? (
          <div className="p-16 text-center space-y-4">
            <div className="w-12 h-12 bg-slate-50 dark:bg-slate-850 rounded-full flex items-center justify-center text-slate-400 mx-auto border border-slate-100 dark:border-slate-850">
              <FileText size={20} />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-350">No customer invoices built</p>
              <p className="text-xs text-slate-550 mt-1">
                Create new invoice files, select clients, and configure line items to request billing.
              </p>
            </div>
            <button 
              onClick={() => navigate('/ar/invoices/new')} 
              className="btn-secondary py-1.5 text-xs inline-flex items-center gap-1 mx-auto"
            >
              <Plus size={12} />
              <span>Launch Builder</span>
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-saas">
              <thead>
                <tr>
                  <th>Invoice #</th>
                  <th>Customer Account</th>
                  <th>Issue Date</th>
                  <th>Due Date</th>
                  <th>Total Amount</th>
                  <th>Status</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map(inv => (
                  <tr key={inv.id || inv._id}>
                    <td>
                      <span className="text-blue-600 dark:text-blue-400 font-mono font-bold text-xs">
                        {inv.invoice_number}
                      </span>
                    </td>
                    <td>
                      <div className="font-semibold text-slate-900 dark:text-white">{inv.customer_name}</div>
                      {inv.customer_email && <div className="text-slate-400 dark:text-slate-500 text-[10px] font-mono mt-0.5">{inv.customer_email}</div>}
                    </td>
                    <td className="text-slate-500 dark:text-slate-400 text-xs font-mono">{inv.issue_date || '—'}</td>
                    <td className="text-slate-500 dark:text-slate-400 text-xs font-mono">{inv.due_date || '—'}</td>
                    <td className="font-mono text-slate-900 dark:text-white font-bold">
                      ${Number(inv.total || inv.grand_total || 0).toFixed(2)}
                      <span className="text-slate-400 text-[10px] uppercase ml-1 font-sans font-medium">{inv.currency || 'USD'}</span>
                    </td>
                    <td>
                      <StatusBadge status={inv.status} />
                    </td>
                    <td className="text-right">
                      <div className="flex justify-end items-center gap-1.5">
                        {inv.status === 'draft' && (
                          <button 
                            onClick={() => handleSend(inv.id || inv._id)} 
                            disabled={updatingId === (inv.id || inv._id)}
                            className="btn-primary py-1 px-2.5 text-[10px] inline-flex items-center gap-1 shadow-sm"
                            title="Mark as Sent"
                          >
                            <Send size={11} />
                            <span>Mark Sent</span>
                          </button>
                        )}
                        {inv.status === 'sent' && (
                          <button 
                            onClick={() => handlePaid(inv.id || inv._id)} 
                            disabled={updatingId === (inv.id || inv._id)}
                            className="btn-primary py-1 px-2.5 text-[10px] inline-flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 shadow-sm"
                            title="Record Payment"
                          >
                            <Check size={11} />
                            <span>Paid</span>
                          </button>
                        )}
                        {updatingId === (inv.id || inv._id) && (
                          <RefreshCw size={12} className="animate-spin text-slate-400" />
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
