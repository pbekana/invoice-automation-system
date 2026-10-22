import React, { useState, useEffect, useCallback } from 'react';
import { getPendingApprovals, approveInvoice, rejectInvoice, requestRevision } from '../services/api';
import { 
  CheckSquare, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  FileText, 
  Building, 
  Sparkles,
  RefreshCw,
  AlertTriangle,
  RotateCcw
} from 'lucide-react';
import useToastStore from '../store/useToastStore';

export default function Approvals() {
  const addToast = useToastStore(state => state.addToast);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionInProgressId, setActionInProgressId] = useState(null);

  // Rejection / Revision modal state
  const [activeActionModal, setActiveActionModal] = useState(null); // { type: 'reject'|'revision', invoice: inv }
  const [actionReason, setActionReason] = useState('');

  const fetchPending = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getPendingApprovals();
      setInvoices(data.invoices || []);
    } catch {
      addToast('Failed to load pending approvals from server.', 'error');
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchPending();
  }, [fetchPending]);

  const handleApprove = async (id) => {
    setActionInProgressId(id);
    try {
      await approveInvoice(id, 'Approved via dashboard queue');
      addToast('Bill approved successfully.', 'success');
      fetchPending();
    } catch (error) {
      addToast(error.response?.data?.error || 'Failed to approve bill.', 'error');
    } finally {
      setActionInProgressId(null);
    }
  };

  const handleActionSubmit = async (e) => {
    e.preventDefault();
    if (!activeActionModal || !actionReason.trim()) return;
    const invId = activeActionModal.invoice.id || activeActionModal.invoice._id;
    setActionInProgressId(invId);

    try {
      if (activeActionModal.type === 'revision') {
        await requestRevision(invId, actionReason.trim());
        addToast('Invoice returned to submitter for revision.', 'success');
      } else {
        await rejectInvoice(invId, actionReason.trim());
        addToast('Invoice rejected.', 'info');
      }
      setActiveActionModal(null);
      setActionReason('');
      fetchPending();
    } catch (error) {
      addToast(error.response?.data?.error || 'Failed to process decision.', 'error');
    } finally {
      setActionInProgressId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-neutral-900 dark:text-white flex items-center gap-2">
            <CheckSquare className="text-blue-600 dark:text-blue-400" />
            Approval Queue
          </h1>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
            Review supplier invoices requiring authorized verification before disbursement.
          </p>
        </div>

        <button
          onClick={fetchPending}
          className="p-2 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 text-neutral-500 hover:text-neutral-900"
          title="Refresh Queue"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-xs text-neutral-400">Loading pending approvals...</div>
      ) : invoices.length === 0 ? (
        <div className="card-premium p-12 text-center bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 flex flex-col items-center justify-center gap-3 max-w-md mx-auto">
          <div className="w-14 h-14 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-500 rounded-full flex items-center justify-center border border-emerald-100 dark:border-emerald-900/40">
            <CheckCircle size={28} />
          </div>
          <div>
            <p className="text-sm font-bold text-neutral-800 dark:text-white">All Caught Up</p>
            <p className="text-xs text-neutral-500 mt-1">
              There are no vendor bills awaiting your approval at this time.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {invoices.map((inv) => {
            const invId = inv.id || inv._id;
            const isProcessing = actionInProgressId === invId;

            return (
              <div 
                key={invId} 
                className="card-premium p-5 bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 flex flex-col justify-between space-y-4"
              >
                <div>
                  {/* Top: Vendor & Amount */}
                  <div className="flex justify-between items-start gap-3 mb-3">
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-bold text-neutral-900 dark:text-white flex items-center gap-1.5 truncate">
                        <Building size={14} className="text-neutral-400 shrink-0" />
                        <span className="truncate">{inv.company || 'Unknown Vendor'}</span>
                      </h3>
                      <p className="text-[10px] text-neutral-400 font-mono mt-0.5">
                        Ref: {inv.invoice_number ? `#${inv.invoice_number}` : invId.slice(-8).toUpperCase()}
                      </p>
                    </div>

                    <div className="text-right shrink-0">
                      <div className="text-base font-bold text-blue-600 dark:text-blue-400 font-mono">
                        ${(inv.total || 0).toFixed(2)}
                      </div>
                      <p className="text-[10px] text-neutral-400">{inv.date || 'Pending Date'}</p>
                    </div>
                  </div>

                  {/* Metadata tags */}
                  <div className="flex items-center gap-2 flex-wrap mb-4">
                    <span className="badge-saas uppercase text-[9px] bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300">
                      {inv.category || 'General'}
                    </span>
                    <span className="text-[10px] text-neutral-400 flex items-center gap-1">
                      <FileText size={11} />
                      <span>Submitter: {inv.submitter_id ? `ID ${inv.submitter_id.slice(-6)}` : 'System'}</span>
                    </span>
                  </div>

                  {/* AI & Matching details */}
                  {inv.confidence !== undefined && (
                    <div className="p-2.5 rounded-lg bg-neutral-50 dark:bg-neutral-950 border border-neutral-100 dark:border-neutral-800 text-[10px] flex items-center justify-between text-neutral-500 mb-2">
                      <span className="flex items-center gap-1">
                        <Sparkles size={11} className="text-blue-500" /> AI Classification Match:
                      </span>
                      <span className="font-mono font-bold text-neutral-800 dark:text-neutral-200">
                        {((inv.confidence || 0.95) * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}

                  {inv.po_match_status && (
                    <div className="text-[10px] font-mono text-neutral-400 flex items-center gap-1">
                      <span>PO Match:</span>
                      <span className="font-semibold text-neutral-600 dark:text-neutral-300 capitalize">
                        {inv.po_match_status.replace('_', ' ')}
                      </span>
                    </div>
                  )}
                </div>

                {/* Actions Row */}
                <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800 flex items-center gap-2 flex-wrap">
                  <button
                    onClick={() => handleApprove(invId)}
                    disabled={isProcessing}
                    className="flex-1 min-w-[100px] btn-primary py-1.5 px-3 text-xs flex items-center justify-center gap-1 bg-emerald-600 hover:bg-emerald-700"
                  >
                    <CheckCircle size={13} />
                    <span>Approve</span>
                  </button>

                  <button
                    onClick={() => {
                      setActiveActionModal({ type: 'revision', invoice: inv });
                      setActionReason('');
                    }}
                    disabled={isProcessing}
                    className="flex-1 min-w-[100px] btn-secondary py-1.5 px-2.5 text-xs flex items-center justify-center gap-1 border-amber-300 dark:border-amber-800 text-amber-700 dark:text-amber-400 hover:bg-amber-50"
                  >
                    <RotateCcw size={13} />
                    <span>Revision</span>
                  </button>

                  <button
                    onClick={() => {
                      setActiveActionModal({ type: 'reject', invoice: inv });
                      setActionReason('');
                    }}
                    disabled={isProcessing}
                    className="flex-1 min-w-[90px] btn-secondary py-1.5 px-2.5 text-xs flex items-center justify-center gap-1 border-rose-200 dark:border-rose-900/30 text-rose-600 hover:bg-rose-50"
                  >
                    <XCircle size={13} />
                    <span>Reject</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Action Dialog for Reject or Request Revision */}
      {activeActionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden p-6 space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-neutral-100 dark:border-neutral-800">
              <h3 className="text-sm font-bold uppercase tracking-wider text-neutral-800 dark:text-white flex items-center gap-1.5">
                {activeActionModal.type === 'revision' ? (
                  <>
                    <RotateCcw size={15} className="text-amber-500" />
                    <span>Return for Correction</span>
                  </>
                ) : (
                  <>
                    <XCircle size={15} className="text-rose-500" />
                    <span>Reject Invoice</span>
                  </>
                )}
              </h3>
              <button onClick={() => setActiveActionModal(null)} className="text-neutral-400 hover:text-neutral-600">
                <AlertCircle size={16} />
              </button>
            </div>

            <form onSubmit={handleActionSubmit} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-[10px] font-bold uppercase text-neutral-500 mb-1">
                  {activeActionModal.type === 'revision' ? 'Notes for Submitter *' : 'Audit Rejection Reason *'}
                </label>
                <textarea
                  rows={3}
                  required
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  placeholder={
                    activeActionModal.type === 'revision'
                      ? 'Explain what items, attachments, or tax calculations need to be corrected...'
                      : 'Specify reason for rejection (e.g. unauthorized spend, duplicate bill)...'
                  }
                  className="input-field text-xs"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-neutral-100 dark:border-neutral-800">
                <button
                  type="button"
                  onClick={() => setActiveActionModal(null)}
                  className="btn-secondary py-1.5 px-3 text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className={`btn-primary py-1.5 px-3 text-xs ${
                    activeActionModal.type === 'revision'
                      ? 'bg-amber-600 hover:bg-amber-700'
                      : 'bg-rose-600 hover:bg-rose-700'
                  }`}
                >
                  {activeActionModal.type === 'revision' ? 'Send Back for Revision' : 'Confirm Rejection'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
