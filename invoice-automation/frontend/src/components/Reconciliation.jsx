import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Scale, 
  Upload, 
  Download, 
  CheckCircle2, 
  AlertTriangle, 
  HelpCircle, 
  RefreshCw, 
  FileText, 
  Calendar, 
  DollarSign,
  ArrowRight,
  ShieldCheck,
  Building
} from 'lucide-react';
import { 
  uploadReconciliationStatement, 
  getReconciliationBatches, 
  getReconciliationBatch 
} from '../services/api';
import useToastStore from '../store/useToastStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export default function Reconciliation() {
  const addToast = useToastStore(state => state.addToast);
  const [batches, setBatches] = useState([]);
  const [activeBatch, setActiveBatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const fetchBatches = useCallback(async (selectFirst = false) => {
    setLoading(true);
    try {
      const data = await getReconciliationBatches();
      setBatches(data.batches || []);
      if (selectFirst && data.batches && data.batches.length > 0) {
        const first = await getReconciliationBatch(data.batches[0].batch_id);
        setActiveBatch(first.batch);
      }
    } catch {
      addToast('Failed to load past reconciliation batches.', 'error');
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchBatches(true);
  }, [fetchBatches]);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const res = await uploadReconciliationStatement(file);
      addToast(`Reconciliation complete: ${res.batch?.matched_count || 0} matched.`, 'success');
      setActiveBatch(res.batch);
      fetchBatches();
    } catch (err) {
      addToast(err.response?.data?.error || 'Failed to process bank statement CSV.', 'error');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleSelectBatch = async (batchId) => {
    try {
      const res = await getReconciliationBatch(batchId);
      setActiveBatch(res.batch);
    } catch {
      addToast('Could not load batch details.', 'error');
    }
  };

  const downloadCSV = (endpoint, filename) => {
    const token = localStorage.getItem('access_token');
    fetch(`${API_BASE_URL}${endpoint}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error('Export failed');
        return res.blob();
      })
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        addToast(`Exported ${filename} successfully.`, 'success');
      })
      .catch(() => addToast(`Failed to export ${filename}.`, 'error'));
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-neutral-900 dark:text-white flex items-center gap-2">
            <Scale className="text-blue-600 dark:text-blue-400" />
            Financial Reconciliation & CSV Exports
          </h1>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
            Reconcile imported bank statement CSVs against recorded payments and export verified financial reports.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="btn-primary py-2 px-3 text-xs flex items-center gap-1.5 shadow-sm"
          >
            <Upload size={14} />
            <span>{uploading ? 'Processing Statement...' : 'Import Statement CSV'}</span>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            className="hidden"
          />
        </div>
      </div>

      {/* CSV Export Quick Actions Grid */}
      <div className="card-premium p-6 bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 space-y-4">
        <div className="flex items-center justify-between border-b border-neutral-100 dark:border-neutral-800 pb-3">
          <div className="flex items-center gap-2">
            <Download className="text-blue-600 dark:text-blue-400 w-4 h-4" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-700 dark:text-neutral-300">
              Authoritative Financial Data Exports
            </h3>
          </div>
          <span className="text-[10px] text-neutral-400">RFC 4180 Compliant CSV</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => downloadCSV('/api/export/invoices', 'invoices_export.csv')}
            className="p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 hover:border-blue-400 hover:bg-blue-50/40 dark:hover:bg-blue-950/20 text-left transition-colors flex items-center justify-between group"
          >
            <div>
              <p className="text-xs font-bold text-neutral-800 dark:text-neutral-200">AP Invoices CSV</p>
              <p className="text-[10px] text-neutral-400 mt-0.5">All bills, statuses, and totals</p>
            </div>
            <Download size={14} className="text-neutral-400 group-hover:text-blue-500 shrink-0" />
          </button>

          <button
            onClick={() => downloadCSV('/api/export/payments', 'payments_export.csv')}
            className="p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 hover:border-emerald-400 hover:bg-emerald-50/40 dark:hover:bg-emerald-950/20 text-left transition-colors flex items-center justify-between group"
          >
            <div>
              <p className="text-xs font-bold text-neutral-800 dark:text-neutral-200">Recorded Payments CSV</p>
              <p className="text-[10px] text-neutral-400 mt-0.5">Authoritative payment ledger</p>
            </div>
            <Download size={14} className="text-neutral-400 group-hover:text-emerald-500 shrink-0" />
          </button>

          <button
            onClick={() => downloadCSV('/api/export/vendors', 'vendors_export.csv')}
            className="p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 hover:border-purple-400 hover:bg-purple-50/40 dark:hover:bg-purple-950/20 text-left transition-colors flex items-center justify-between group"
          >
            <div>
              <p className="text-xs font-bold text-neutral-800 dark:text-neutral-200">Vendors Directory CSV</p>
              <p className="text-[10px] text-neutral-400 mt-0.5">Master supplier profiles</p>
            </div>
            <Download size={14} className="text-neutral-400 group-hover:text-purple-500 shrink-0" />
          </button>

          <button
            onClick={() => downloadCSV('/api/export/customers', 'customers_export.csv')}
            className="p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 hover:border-cyan-400 hover:bg-cyan-50/40 dark:hover:bg-cyan-950/20 text-left transition-colors flex items-center justify-between group"
          >
            <div>
              <p className="text-xs font-bold text-neutral-800 dark:text-neutral-200">Customers CSV</p>
              <p className="text-[10px] text-neutral-400 mt-0.5">Customer master & terms</p>
            </div>
            <Download size={14} className="text-neutral-400 group-hover:text-cyan-500 shrink-0" />
          </button>
        </div>
      </div>

      {/* Main Reconciliation Section */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Past Batches Sidebar */}
        <div className="card-premium p-4 bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 flex flex-col h-[520px]">
          <div className="flex items-center justify-between pb-3 border-b border-neutral-100 dark:border-neutral-800">
            <span className="text-xs font-bold uppercase tracking-wider text-neutral-500">Import Batches</span>
            <button onClick={fetchBatches} className="text-neutral-400 hover:text-neutral-600 p-1">
              <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-neutral-100 dark:divide-neutral-800 mt-2 space-y-1">
            {batches.length === 0 ? (
              <p className="text-xs text-neutral-400 p-4 text-center">No statements imported yet.</p>
            ) : (
              batches.map((b) => (
                <button
                  key={b.batch_id}
                  onClick={() => handleSelectBatch(b.batch_id)}
                  className={`w-full text-left p-3 rounded-xl transition-all ${
                    activeBatch?.batch_id === b.batch_id
                      ? 'bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900/40'
                      : 'hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
                  }`}
                >
                  <div className="flex justify-between items-center text-xs font-bold text-neutral-800 dark:text-neutral-200">
                    <span className="font-mono">{b.batch_id}</span>
                    <span className="text-[10px] text-emerald-600 font-semibold">{b.matched_count} matched</span>
                  </div>
                  <p className="text-[10px] text-neutral-400 truncate mt-0.5">{b.filename}</p>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Batch Details & Transactions Table */}
        <div className="lg:col-span-3 card-premium p-6 bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 flex flex-col justify-between">
          {activeBatch ? (
            <div className="space-y-4">
              {/* Batch Summary Header */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-4 border-b border-neutral-100 dark:border-neutral-800">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-neutral-900 dark:text-white font-mono">
                      {activeBatch.batch_id}
                    </h3>
                    <span className="text-xs text-neutral-400">({activeBatch.filename})</span>
                  </div>
                  <p className="text-xs text-neutral-500 mt-0.5">
                    Total: {activeBatch.total_count} transactions processed
                  </p>
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-bold border border-emerald-200 dark:border-emerald-900/40">
                    ✓ {activeBatch.matched_count} Matched
                  </span>
                  <span className="px-2.5 py-1 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 font-bold border border-amber-200 dark:border-amber-900/40">
                    ⚠ {activeBatch.ambiguous_count} Ambiguous
                  </span>
                  <span className="px-2.5 py-1 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 font-bold">
                    ✕ {activeBatch.unmatched_count} Unmatched
                  </span>
                </div>
              </div>

              {/* Transactions Table with Overflow protection */}
              <div className="overflow-x-auto rounded-xl border border-neutral-200 dark:border-neutral-800">
                <table className="table-saas min-w-[650px]">
                  <thead>
                    <tr>
                      <th>TX Ref / Date</th>
                      <th>Statement Reference</th>
                      <th>Amount</th>
                      <th>Status</th>
                      <th>Matching Diagnostic</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(activeBatch.items || []).map((tx) => (
                      <tr key={tx.tx_id}>
                        <td>
                          <div className="font-mono text-xs font-semibold text-neutral-800 dark:text-neutral-200">{tx.tx_id}</div>
                          <div className="text-[10px] text-neutral-400">{tx.date}</div>
                        </td>
                        <td className="text-xs text-neutral-700 dark:text-neutral-300 max-w-xs truncate">
                          {tx.reference || '—'}
                        </td>
                        <td className="font-mono font-bold text-xs text-blue-600 dark:text-blue-400">
                          ${(tx.amount || 0).toFixed(2)}
                        </td>
                        <td>
                          <span className={`badge-saas text-[10px] uppercase font-bold ${
                            tx.status === 'matched' 
                              ? 'badge-saas-green' 
                              : tx.status === 'ambiguous' 
                                ? 'badge-saas-yellow' 
                                : 'badge-saas-gray'
                          }`}>
                            {tx.status}
                          </span>
                        </td>
                        <td className="text-xs text-neutral-500">
                          {tx.notes}
                          {tx.matched_payment_ref && (
                            <span className="block text-[10px] text-emerald-600 font-mono mt-0.5">
                              Payment: {tx.matched_payment_ref}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="text-center py-20 space-y-3">
              <Scale size={32} className="mx-auto text-neutral-400" />
              <p className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">
                No Reconciliation Statement Selected
              </p>
              <p className="text-xs text-neutral-400 max-w-sm mx-auto">
                Upload a bank statement CSV with Date, Description/Reference, and Amount columns to begin reconciliation.
              </p>
            </div>
          )}

          {/* Compliance Disclaimer Notice */}
          <div className="mt-6 pt-4 border-t border-neutral-100 dark:border-neutral-800 flex items-center gap-2 text-[11px] text-neutral-400">
            <ShieldCheck size={14} className="text-emerald-500 shrink-0" />
            <span>
              Internal Control: Reconciles imported statement records against internal payment vouchers. Live bank webhooks or executing transfers require external payment gateway configuration.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
