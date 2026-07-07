import React, { useState, useEffect } from 'react';
import { getPendingApprovals, approveInvoice, rejectInvoice } from '../services/api';
import { CheckCircle, XCircle, Clock, FileText, AlertCircle, ShieldAlert, Sparkles, Building, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import useToastStore from '../store/useToastStore';

const Approvals = () => {
  const addToast = useToastStore(state => state.addToast);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processingId, setProcessingId] = useState(null);
  
  // Rejection logic state
  const [rejectingId, setRejectingId] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');

  const fetchApprovals = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getPendingApprovals();
      setInvoices(Array.isArray(data) ? data : data.invoices || []);
    } catch (err) {
      if (err.response?.status === 403) {
        setError("Access Denied: You do not have the required role (approver or admin) to process pending invoice approvals.");
      } else {
        setError('Failed to fetch pending approvals from the server.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, []);

  const handleApprove = async (id) => {
    setProcessingId(id);
    try {
      await approveInvoice(id, 'Approved via dashboard workflow queue');
      addToast('Invoice approved successfully.', 'success');
      fetchApprovals();
    } catch (err) {
      addToast('Failed to approve invoice: ' + (err.response?.data?.error || err.message), 'error');
    } finally {
      setProcessingId(null);
    }
  };

  const handleRejectSubmit = async (e) => {
    e.preventDefault();
    if (!rejectionReason.trim()) return;

    const id = rejectingId;
    setProcessingId(id);
    try {
      await rejectInvoice(id, rejectionReason);
      setRejectingId(null);
      setRejectionReason('');
      addToast('Invoice rejected and reason recorded.', 'info');
      fetchApprovals();
    } catch (err) {
      addToast('Failed to reject invoice: ' + (err.response?.data?.error || err.message), 'error');
    } finally {
      setProcessingId(null);
    }
  };

  if (error) {
    return (
      <div className="card-premium p-6 bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900/40 text-amber-800 dark:text-amber-200 flex items-start gap-3.5 max-w-2xl mx-auto mt-6">
        <ShieldAlert size={20} className="shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider">Workflow Authorization Error</h3>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
          <Clock className="text-blue-500" /> Approvals Workspace
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Review, approve, or reject vendor bills based on configured financial authorization thresholds
        </p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2].map((n) => (
            <div key={n} className="card-premium p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 animate-pulse space-y-4">
              <div className="flex justify-between items-center">
                <div className="w-1/2 h-4 bg-slate-200 dark:bg-slate-800 rounded" />
                <div className="w-16 h-5 bg-slate-200 dark:bg-slate-800 rounded" />
              </div>
              <div className="w-1/3 h-3 bg-slate-200 dark:bg-slate-800 rounded" />
              <div className="h-[1px] bg-slate-100 dark:bg-slate-800" />
              <div className="flex gap-2">
                <div className="flex-1 h-9 bg-slate-200 dark:bg-slate-800 rounded" />
                <div className="flex-1 h-9 bg-slate-200 dark:bg-slate-800 rounded" />
              </div>
            </div>
          ))}
        </div>
      ) : invoices.length === 0 ? (
        <div className="card-premium p-12 text-center bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 flex flex-col items-center justify-center gap-4 max-w-lg mx-auto">
          <div className="w-16 h-16 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-500 rounded-full flex items-center justify-center border border-emerald-100 dark:border-emerald-900/30">
            <CheckCircle size={32} />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-800 dark:text-white">Workspace Clean</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              You are all caught up! There are no pending vendor bills awaiting your approval.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {invoices.map((inv) => (
            <div 
              key={inv.id || inv._id} 
              className="card-premium p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 flex flex-col justify-between"
            >
              <div>
                {/* Card Title & Amount */}
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                      <Building size={16} className="text-slate-400" />
                      <span>{inv.company || 'Unknown Vendor'}</span>
                    </h3>
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 font-mono mt-0.5">
                      ID: {(inv.id || inv._id).slice(-8).toUpperCase()}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-blue-600 dark:text-blue-400 font-mono">
                      ${inv.total?.toFixed(2)}
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">{inv.date}</p>
                  </div>
                </div>

                {/* Submitter & Category */}
                <div className="flex items-center gap-2 mb-6">
                  <span className={`badge-saas text-[9px] uppercase ${
                    inv.category?.toLowerCase() === 'software' ? 'badge-saas-blue' :
                    inv.category?.toLowerCase() === 'supplies' ? 'badge-saas-green' :
                    inv.category?.toLowerCase() === 'food' ? 'badge-saas-yellow' : 'badge-saas-gray'
                  }`}>
                    {inv.category || 'Other'}
                  </span>
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 flex items-center gap-1">
                    <FileText size={12} className="text-slate-300 dark:text-slate-700" /> 
                    <span>Submitter: {inv.submitter_id ? `User ID ${inv.submitter_id.slice(-6)}` : 'System'}</span>
                  </span>
                </div>

                {/* AI prediction indicator */}
                {inv.confidence !== undefined && (
                  <div className="mb-6 p-2.5 bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-100 dark:border-slate-800 text-[10px] flex items-center justify-between text-slate-500 dark:text-slate-400">
                    <span className="flex items-center gap-1 font-medium">
                      <Sparkles size={12} className="text-blue-500" /> AI Confidence Match:
                    </span>
                    <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                      {(inv.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>

              {/* Action Buttons / Rejection Forms */}
              <div className="border-t border-slate-100 dark:border-slate-800 pt-4 mt-auto">
                <AnimatePresence mode="wait">
                  {rejectingId === (inv.id || inv._id) ? (
                    <motion.form 
                      key="reject-form"
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      onSubmit={handleRejectSubmit}
                      className="space-y-3"
                    >
                      <div>
                        <label className="block text-[10px] font-bold uppercase tracking-wider text-rose-500">
                          Rejection Comments
                        </label>
                        <input
                          type="text"
                          required
                          value={rejectionReason}
                          onChange={(e) => setRejectionReason(e.target.value)}
                          placeholder="Provide audit reason (e.g. Total mismatched, invalid category)"
                          className="input-field mt-1.5 py-1.5 text-xs border-rose-300 dark:border-rose-900/50 focus:ring-rose-500"
                        />
                      </div>
                      <div className="flex gap-2 justify-end">
                        <button
                          type="button"
                          onClick={() => {
                            setRejectingId(null);
                            setRejectionReason('');
                          }}
                          className="btn-secondary py-1 text-[10px]"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={processingId === (inv.id || inv._id)}
                          className="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-[10px] font-semibold"
                        >
                          Confirm Reject
                        </button>
                      </div>
                    </motion.form>
                  ) : (
                    <motion.div 
                      key="action-buttons"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex gap-3"
                    >
                      <button
                        onClick={() => handleApprove(inv.id || inv._id)}
                        disabled={processingId === (inv.id || inv._id)}
                        className="flex-1 btn-primary py-2 text-xs flex items-center justify-center gap-1.5 bg-emerald-600 hover:bg-emerald-700"
                      >
                        <CheckCircle size={14} /> 
                        <span>{processingId === (inv.id || inv._id) ? 'Processing...' : 'Approve Bill'}</span>
                      </button>
                      <button
                        onClick={() => setRejectingId(inv.id || inv._id)}
                        disabled={processingId === (inv.id || inv._id)}
                        className="flex-1 btn-secondary py-2 text-xs flex items-center justify-center gap-1.5 border-rose-200 dark:border-rose-900/30 hover:bg-rose-50 dark:hover:bg-rose-950/20 text-rose-600 dark:text-rose-400"
                      >
                        <XCircle size={14} /> 
                        <span>Reject</span>
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Approvals;
