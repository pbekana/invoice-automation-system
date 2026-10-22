import React, { useState, useEffect, useCallback } from 'react';
import { 
  getInvoices, 
  submitInvoice, 
  recordInvoicePayment, 
  getInvoicePayments,
  getInvoiceHistory,
  cancelInvoice
} from '../services/api';
import UploadInvoice from './UploadInvoice';
import { 
  FileText, 
  Search, 
  Filter, 
  ArrowRight, 
  CheckCircle, 
  Clock, 
  XCircle, 
  AlertCircle, 
  Upload, 
  X, 
  Plus, 
  RefreshCw,
  Building,
  Calendar,
  CreditCard,
  DollarSign,
  AlertTriangle
} from 'lucide-react';
import useAuthStore from '../store/useAuthStore';
import useToastStore from '../store/useToastStore';

const StatusBadge = ({ status, isOverdue }) => {
  const styles = {
    draft: 'badge-saas-gray',
    submitted: 'badge-saas-blue border-blue-200 dark:border-blue-900/30',
    pending_approval: 'badge-saas-yellow border-yellow-200 dark:border-yellow-900/30',
    approved: 'badge-saas-green border-green-200 dark:border-green-900/30',
    needs_revision: 'badge-saas-yellow bg-amber-50 text-amber-700 border-amber-300 dark:border-amber-900/40',
    partially_paid: 'badge-saas-blue bg-sky-50 text-sky-700 border-sky-300 dark:border-sky-900/40',
    paid: 'badge-saas-green font-bold border-green-300 dark:border-green-800/40',
    rejected: 'badge-saas-red border-red-200 dark:border-red-900/30',
    cancelled: 'badge-saas-gray',
  };

  const icons = {
    draft: <FileText size={11} />,
    submitted: <ArrowRight size={11} />,
    pending_approval: <Clock size={11} />,
    approved: <CheckCircle size={11} />,
    needs_revision: <AlertTriangle size={11} />,
    partially_paid: <CreditCard size={11} />,
    paid: <CheckCircle size={11} />,
    rejected: <XCircle size={11} />,
    cancelled: <AlertCircle size={11} />,
  };

  return (
    <div className="inline-flex items-center gap-1.5 flex-wrap">
      <span className={`badge-saas border gap-1 px-2 py-0.5 text-[10px] ${styles[status] || styles.draft}`}>
        {icons[status] || <FileText size={11} />}
        <span>{(status || 'draft').replace('_', ' ').toUpperCase()}</span>
      </span>
      {isOverdue && status !== 'paid' && status !== 'cancelled' && (
        <span className="badge-saas text-[9px] bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-800 font-bold">
          OVERDUE
        </span>
      )}
    </div>
  );
};

export default function Invoices({ refreshTrigger = 0 }) {
  const user = useAuthStore(state => state.user);
  const addToast = useToastStore(state => state.addToast);

  const roles = user?.roles || [];
  const isViewer = roles.length === 1 && roles[0] === 'viewer';
  const canUpload = !isViewer;
  const canPay = roles.includes('admin') || roles.includes('finance') || roles.includes('finance_user');

  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [submittingId, setSubmittingId] = useState(null);
  const [cancellingId, setCancellingId] = useState(null);
  const [uploadDrawerOpen, setUploadDrawerOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [invoiceHistory, setInvoiceHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Payment recording state
  const [payModalInvoice, setPayModalInvoice] = useState(null);
  const [payAmount, setPayAmount] = useState('');
  const [payMethod, setPayMethod] = useState('bank_transfer');
  const [payRef, setPayRef] = useState('');
  const [payNotes, setPayNotes] = useState('');
  const [recordingPay, setRecordingPay] = useState(false);
  const [invoicePayments, setInvoicePayments] = useState([]);

  useEffect(() => {
    if (selectedInvoice) {
      const invId = selectedInvoice.id || selectedInvoice._id;
      setHistoryLoading(true);
      getInvoiceHistory(invId)
        .then(res => {
          const list = (res.status_history && res.status_history.length > 0)
            ? res.status_history
            : (selectedInvoice.status_history || []);
          setInvoiceHistory(list);
        })
        .catch(err => {
          console.error('Failed to load status history:', err);
          setInvoiceHistory(selectedInvoice.status_history || []);
        })
        .finally(() => setHistoryLoading(false));
    } else {
      setInvoiceHistory([]);
    }
  }, [selectedInvoice]);

  const fetchInvoices = useCallback(async () => {
    setLoading(true);
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const data = await getInvoices(params);
      setInvoices(Array.isArray(data) ? data : data.invoices || []);
    } catch (error) {
      console.error('Failed to fetch invoices:', error);
      addToast('Failed to load invoices from server.', 'error');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, addToast]);

  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices, refreshTrigger]);

  const handleSubmit = async (id) => {
    setSubmittingId(id);
    try {
      await submitInvoice(id);
      addToast('Invoice submitted for approval queue.', 'success');
      fetchInvoices();
      if (selectedInvoice && (selectedInvoice.id === id || selectedInvoice._id === id)) {
        setSelectedInvoice(null);
      }
    } catch (error) {
      addToast(error.response?.data?.error || 'Failed to submit invoice.', 'error');
    } finally {
      setSubmittingId(null);
    }
  };

  const handleCancel = async (id) => {
    const reason = window.prompt('Please enter the cancellation reason:');
    if (!reason || !reason.trim()) return;

    setCancellingId(id);
    try {
      await cancelInvoice(id, reason.trim());
      addToast('Invoice cancelled successfully.', 'success');
      fetchInvoices();
      if (selectedInvoice && (selectedInvoice.id === id || selectedInvoice._id === id)) {
        setSelectedInvoice(null);
      }
    } catch (error) {
      addToast(error.response?.data?.error || 'Failed to cancel invoice.', 'error');
    } finally {
      setCancellingId(null);
    }
  };

  const openPaymentModal = async (inv) => {
    setPayModalInvoice(inv);
    const bal = inv.outstanding_balance !== undefined ? inv.outstanding_balance : inv.total;
    setPayAmount(bal ? bal.toFixed(2) : '0.00');
    setPayRef(`REF-${Date.now().toString().slice(-6)}`);
    setPayNotes('');
    try {
      const hist = await getInvoicePayments(inv.id || inv._id, 'payable');
      setInvoicePayments(hist.payments || []);
    } catch {
      setInvoicePayments([]);
    }
  };

  const handleRecordPayment = async (e) => {
    e.preventDefault();
    if (!payModalInvoice) return;
    const invId = payModalInvoice.id || payModalInvoice._id;
    const amountVal = parseFloat(payAmount);

    if (isNaN(amountVal) || amountVal <= 0) {
      addToast('Please enter a valid positive payment amount.', 'error');
      return;
    }

    setRecordingPay(true);
    try {
      await recordInvoicePayment(invId, {
        amount: amountVal,
        payment_method: payMethod,
        reference: payRef,
        notes: payNotes,
        type: 'payable'
      });
      addToast(`Payment of $${amountVal.toFixed(2)} recorded successfully.`, 'success');
      setPayModalInvoice(null);
      fetchInvoices();
    } catch (err) {
      addToast(err.response?.data?.error || 'Failed to record payment.', 'error');
    } finally {
      setRecordingPay(false);
    }
  };

  const filteredInvoices = invoices.filter(inv => {
    const query = searchQuery.toLowerCase();
    const company = (inv.company || inv.vendor_name || '').toLowerCase();
    const invoiceNum = (inv.invoice_number || '').toLowerCase();
    const category = (inv.category || '').toLowerCase();
    return company.includes(query) || invoiceNum.includes(query) || category.includes(query);
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-neutral-900 dark:text-white flex items-center gap-2">
            <FileText className="text-blue-600 dark:text-blue-400" /> Accounts Payable Bills
          </h1>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
            Supplier bills ingested via OCR, matching rules, multi-tier approvals, and payment recording
          </p>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {canUpload && (
            <button
              onClick={() => setUploadDrawerOpen(true)}
              className="btn-primary flex-1 sm:flex-initial py-2 px-3 text-xs flex items-center justify-center gap-1.5 shadow-sm"
            >
              <Upload size={14} />
              <span>Upload New Bill</span>
            </button>
          )}
          <button
            onClick={fetchInvoices}
            className="p-2 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 text-neutral-500 hover:text-neutral-900"
            title="Refresh List"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" size={15} />
          <input
            type="text"
            placeholder="Search by vendor, invoice number, or category..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field pl-9 text-xs"
          />
          {searchQuery && (
            <button 
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
            >
              <X size={14} />
            </button>
          )}
        </div>

        <div className="w-full sm:w-56 relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" size={14} />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input-field pl-9 pr-8 text-xs appearance-none cursor-pointer"
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="submitted">Submitted</option>
            <option value="pending_approval">Pending Approval</option>
            <option value="needs_revision">Needs Revision</option>
            <option value="approved">Approved</option>
            <option value="partially_paid">Partially Paid</option>
            <option value="paid">Paid</option>
            <option value="rejected">Rejected</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none border-l-4 border-r-4 border-t-4 border-transparent border-t-neutral-400" />
        </div>
      </div>

      {/* Main Table Grid */}
      <div className="card-premium overflow-hidden bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800">
        {loading ? (
          <div className="p-12 text-center text-xs text-neutral-400">Loading invoices...</div>
        ) : filteredInvoices.length === 0 ? (
          <div className="p-16 text-center space-y-3">
            <div className="w-12 h-12 bg-neutral-100 dark:bg-neutral-800 rounded-full flex items-center justify-center text-neutral-400 mx-auto">
              <FileText size={20} />
            </div>
            <div>
              <p className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">No bills found</p>
              <p className="text-xs text-neutral-500 mt-1">
                {searchQuery || statusFilter 
                  ? 'Try adjusting your search criteria or status filter'
                  : 'Get started by uploading a vendor bill or invoice.'}
              </p>
            </div>
            {!searchQuery && !statusFilter && canUpload && (
              <button 
                onClick={() => setUploadDrawerOpen(true)}
                className="btn-secondary py-1.5 text-xs inline-flex items-center gap-1"
              >
                <Plus size={12} />
                <span>Upload first bill</span>
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-saas min-w-[720px]">
              <thead>
                <tr>
                  <th>Vendor / Reference</th>
                  <th>Bill Date</th>
                  <th>Category</th>
                  <th>Total / Outstanding</th>
                  <th>Status</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredInvoices.map((inv) => {
                  const invId = inv.id || inv._id;
                  const isOwner = inv.submitter_id && user?.id && String(inv.submitter_id) === String(user.id);
                  const canSubmitThis = (roles.includes('admin') || isOwner) && ['draft', 'rejected', 'needs_revision'].includes(inv.status);
                  const canCancelThis = (roles.includes('admin') || isOwner) && ['submitted', 'pending_approval', 'draft'].includes(inv.status);
                  const canPayThis = canPay && ['approved', 'partially_paid'].includes(inv.status);
                  const bal = inv.outstanding_balance !== undefined ? inv.outstanding_balance : (inv.status === 'paid' ? 0 : inv.total);

                  return (
                    <tr key={invId} className="group hover:bg-neutral-50/70 dark:hover:bg-neutral-800/40">
                      <td>
                        <div className="font-semibold text-xs text-neutral-900 dark:text-neutral-100 flex items-center gap-1.5">
                          <span className="truncate max-w-[200px]">{inv.company || 'Unknown Vendor'}</span>
                          {inv.invoice_number && (
                            <span className="text-[10px] text-neutral-500 font-mono bg-neutral-100 dark:bg-neutral-800 px-1 py-0.5 rounded shrink-0">
                              #{inv.invoice_number}
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] text-neutral-400 mt-0.5">
                          {inv.purchase_order_number ? `PO: ${inv.purchase_order_number}` : 'Standard Bill'}
                        </div>
                      </td>
                      <td className="text-neutral-500 font-mono text-xs whitespace-nowrap">
                        {inv.date || 'Pending'}
                      </td>
                      <td>
                        <span className="badge-saas uppercase text-[9px] bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300">
                          {inv.category || 'General'}
                        </span>
                      </td>
                      <td>
                        <div className="font-mono text-xs text-neutral-900 dark:text-neutral-100 font-bold">
                          ${(inv.total || 0).toFixed(2)}
                        </div>
                        {['approved', 'partially_paid'].includes(inv.status) && (
                          <div className="text-[10px] font-mono text-amber-600 dark:text-amber-400">
                            Bal: ${bal.toFixed(2)}
                          </div>
                        )}
                      </td>
                      <td>
                        <StatusBadge status={inv.status} isOverdue={inv.is_overdue} />
                      </td>
                      <td className="text-right whitespace-nowrap">
                        <div className="flex justify-end items-center gap-1.5">
                          <button 
                            onClick={() => setSelectedInvoice(inv)}
                            className="p-1.5 rounded-lg border border-neutral-200 dark:border-neutral-800 hover:bg-neutral-100 text-neutral-600 text-xs"
                            title="Inspect Details"
                          >
                            Details
                          </button>
                          
                          {canSubmitThis && (
                            <button
                              onClick={() => handleSubmit(invId)}
                              disabled={submittingId === invId}
                              className="btn-primary py-1 px-2.5 text-[11px]"
                            >
                              {submittingId === invId ? 'Submitting...' : 'Submit'}
                            </button>
                          )}

                          {canCancelThis && (
                            <button
                              onClick={() => handleCancel(invId)}
                              disabled={cancellingId === invId}
                              className="px-2 py-1 text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg border border-rose-200 dark:border-rose-900/40 text-[11px] font-medium"
                              title="Cancel Invoice"
                            >
                              {cancellingId === invId ? 'Cancelling...' : 'Cancel'}
                            </button>
                          )}

                          {canPayThis && (
                            <button
                              onClick={() => openPaymentModal(inv)}
                              className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-[11px] font-semibold flex items-center gap-1"
                            >
                              <DollarSign size={11} />
                              <span>Record Pay</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Slide-over Drawer for Upload */}
      {uploadDrawerOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
            onClick={() => setUploadDrawerOpen(false)}
          />
          <div className="fixed inset-y-0 right-0 w-full max-w-md bg-white dark:bg-neutral-900 border-l border-neutral-200 dark:border-neutral-800 shadow-2xl p-6 flex flex-col justify-between overflow-y-auto">
            <div>
              <div className="flex justify-between items-center mb-6">
                <span className="text-xs font-bold uppercase tracking-wider text-neutral-400">Document Ingestion</span>
                <button 
                  onClick={() => setUploadDrawerOpen(false)}
                  className="p-1 rounded-md text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800"
                >
                  <X size={16} />
                </button>
              </div>
              <UploadInvoice onUploadSuccess={() => {
                fetchInvoices();
                setTimeout(() => setUploadDrawerOpen(false), 1500);
              }} />
            </div>
          </div>
        </div>
      )}

      {/* Invoice Details Dialog Modal */}
      {selectedInvoice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden p-6 space-y-4">
            <div className="flex justify-between items-start pb-3 border-b border-neutral-100 dark:border-neutral-800">
              <div>
                <h3 className="text-base font-bold text-neutral-900 dark:text-white">
                  Invoice Summary
                </h3>
                <p className="text-xs text-neutral-400 font-mono">
                  ID: {selectedInvoice.id || selectedInvoice._id}
                </p>
              </div>
              <button 
                onClick={() => setSelectedInvoice(null)}
                className="text-neutral-400 hover:text-neutral-600"
              >
                <X size={16} />
              </button>
            </div>

            <div className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-950 border border-neutral-100 dark:border-neutral-800 space-y-1">
                  <span className="text-[10px] uppercase text-neutral-400 font-bold flex items-center gap-1">
                    <Building size={11} /> Vendor
                  </span>
                  <p className="font-bold text-neutral-800 dark:text-neutral-200">{selectedInvoice.company || 'Unknown'}</p>
                  <p className="text-[10px] text-neutral-400">Invoice: #{selectedInvoice.invoice_number || 'N/A'}</p>
                </div>

                <div className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-950 border border-neutral-100 dark:border-neutral-800 space-y-1">
                  <span className="text-[10px] uppercase text-neutral-400 font-bold flex items-center gap-1">
                    <Calendar size={11} /> Dates & Terms
                  </span>
                  <p className="font-mono text-neutral-800 dark:text-neutral-200">Date: {selectedInvoice.date || 'N/A'}</p>
                  <p className="font-mono text-neutral-400">Due: {selectedInvoice.due_date || 'N/A'}</p>
                </div>
              </div>

              <div className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50/50 dark:bg-neutral-900/50 flex justify-between items-center">
                <div>
                  <span className="text-[11px] text-neutral-400">Total Billed Amount</span>
                  <p className="text-xs text-neutral-500">Currency: {selectedInvoice.currency || 'USD'}</p>
                </div>
                <span className="text-xl font-mono font-bold text-blue-600 dark:text-blue-400">
                  ${(selectedInvoice.total || 0).toFixed(2)}
                </span>
              </div>

              {/* Status History / Audit Trail */}
              <div className="space-y-1.5 pt-2 border-t border-neutral-100 dark:border-neutral-800">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider flex items-center gap-1.5">
                    <Clock size={11} className="text-blue-500" />
                    <span>Status History (Audit Trail)</span>
                  </span>
                  <span className="text-[10px] text-neutral-400 font-mono">
                    {invoiceHistory.length} {invoiceHistory.length === 1 ? 'record' : 'records'}
                  </span>
                </div>

                {historyLoading ? (
                  <div className="py-3 text-center text-xs text-neutral-400">Loading audit history...</div>
                ) : invoiceHistory.length === 0 ? (
                  <div className="p-3 text-center text-xs text-neutral-400 bg-neutral-50 dark:bg-neutral-950 rounded-xl border border-neutral-100 dark:border-neutral-800">
                    No status history recorded yet.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                    {invoiceHistory.map((entry, idx) => (
                      <div key={idx} className="p-2 rounded-xl bg-neutral-50 dark:bg-neutral-950 border border-neutral-100 dark:border-neutral-800 text-[11px] space-y-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1 font-semibold">
                            <span className="px-1.5 py-0.5 rounded text-[9px] bg-neutral-200 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 uppercase">
                              {entry.previous_status || 'initial'}
                            </span>
                            <ArrowRight size={10} className="text-neutral-400" />
                            <span className="px-1.5 py-0.5 rounded text-[9px] bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 uppercase font-bold">
                              {entry.new_status}
                            </span>
                          </div>
                          <span className="text-[10px] text-neutral-400 font-mono">
                            {entry.timestamp ? new Date(entry.timestamp).toLocaleString() : ''}
                          </span>
                        </div>
                        <div className="text-[10px] text-neutral-500 flex justify-between">
                          <span>
                            By: <strong className="text-neutral-700 dark:text-neutral-300">{entry.user_name || entry.user_email || entry.user_id || 'System'}</strong>
                            {entry.role && <span className="ml-1 text-neutral-400 font-mono">({entry.role})</span>}
                          </span>
                        </div>
                        {(entry.reason || entry.comment) && (
                          <div className="text-[10px] text-neutral-600 dark:text-neutral-400 italic bg-white dark:bg-neutral-900 px-2 py-0.5 rounded border border-neutral-100 dark:border-neutral-800">
                            "{entry.reason || entry.comment}"
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-between items-center gap-2 pt-3 border-t border-neutral-100 dark:border-neutral-800">
              <div>
                {(roles.includes('admin') || (selectedInvoice.submitter_id && String(selectedInvoice.submitter_id) === String(user?.id))) && 
                  ['submitted', 'pending_approval', 'draft'].includes(selectedInvoice.status) && (
                  <button
                    onClick={() => handleCancel(selectedInvoice.id || selectedInvoice._id)}
                    disabled={cancellingId === (selectedInvoice.id || selectedInvoice._id)}
                    className="px-2.5 py-1 text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg border border-rose-200 dark:border-rose-900/40 text-xs font-semibold"
                  >
                    {cancellingId === (selectedInvoice.id || selectedInvoice._id) ? 'Cancelling...' : 'Cancel Invoice'}
                  </button>
                )}
              </div>
              <button 
                onClick={() => setSelectedInvoice(null)}
                className="btn-secondary py-1.5 text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Record Payment Modal */}
      {payModalInvoice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden p-6 space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-neutral-100 dark:border-neutral-800">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-neutral-800 dark:text-white flex items-center gap-1.5">
                  <CreditCard size={15} className="text-emerald-500" />
                  <span>Record Payment Voucher</span>
                </h3>
                <p className="text-[10px] text-neutral-400 mt-0.5">
                  Records an external disbursement; does not initiate direct bank debits.
                </p>
              </div>
              <button onClick={() => setPayModalInvoice(null)} className="text-neutral-400 hover:text-neutral-600">
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleRecordPayment} className="space-y-3.5 text-xs">
              <div className="p-3 bg-neutral-50 dark:bg-neutral-950 rounded-xl border border-neutral-100 dark:border-neutral-800 flex justify-between items-center">
                <div>
                  <span className="text-[10px] uppercase text-neutral-400 font-bold">Outstanding Balance</span>
                  <p className="text-xs font-semibold text-neutral-700 dark:text-neutral-300">
                    Vendor: {payModalInvoice.company}
                  </p>
                </div>
                <span className="text-base font-mono font-bold text-amber-600 dark:text-amber-400">
                  ${(payModalInvoice.outstanding_balance !== undefined ? payModalInvoice.outstanding_balance : payModalInvoice.total).toFixed(2)}
                </span>
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase text-neutral-500 mb-1">
                  Payment Amount ($) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={payAmount}
                  onChange={(e) => setPayAmount(e.target.value)}
                  className="input-field text-xs font-mono font-bold"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-bold uppercase text-neutral-500 mb-1">
                    Method *
                  </label>
                  <select
                    value={payMethod}
                    onChange={(e) => setPayMethod(e.target.value)}
                    className="input-field text-xs cursor-pointer"
                  >
                    <option value="bank_transfer">Bank Wire / ACH</option>
                    <option value="check">Company Check</option>
                    <option value="credit_card">Corporate Card</option>
                    <option value="cash">Cash / Petty</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-bold uppercase text-neutral-500 mb-1">
                    Reference / Check #
                  </label>
                  <input
                    type="text"
                    required
                    value={payRef}
                    onChange={(e) => setPayRef(e.target.value)}
                    placeholder="WIRE-10492"
                    className="input-field text-xs font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase text-neutral-500 mb-1">
                  Internal Notes / Memo
                </label>
                <textarea
                  rows={2}
                  value={payNotes}
                  onChange={(e) => setPayNotes(e.target.value)}
                  placeholder="Processed via accounts payable batch"
                  className="input-field text-xs"
                />
              </div>

              {invoicePayments.length > 0 && (
                <div className="space-y-1">
                  <span className="text-[10px] uppercase font-bold text-neutral-400">Past Payments On This Bill</span>
                  <div className="max-h-24 overflow-y-auto space-y-1 p-2 rounded-lg bg-neutral-50 dark:bg-neutral-950 border border-neutral-100 dark:border-neutral-800 text-[10px]">
                    {invoicePayments.map((p, i) => (
                      <div key={i} className="flex justify-between font-mono">
                        <span>{p.payment_date}: ${p.amount.toFixed(2)} ({p.payment_method})</span>
                        <span className="text-neutral-400">{p.transaction_reference}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-3 border-t border-neutral-100 dark:border-neutral-800">
                <button
                  type="button"
                  onClick={() => setPayModalInvoice(null)}
                  className="btn-secondary py-1.5 px-3 text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={recordingPay}
                  className="btn-primary py-1.5 px-3 text-xs bg-emerald-600 hover:bg-emerald-700"
                >
                  {recordingPay ? 'Saving Payment...' : 'Confirm Payment Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
