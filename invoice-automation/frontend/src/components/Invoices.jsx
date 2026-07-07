import React, { useState, useEffect } from 'react';
import { getInvoices, submitInvoice } from '../services/api';
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
  Layers,
  ChevronRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const StatusBadge = ({ status }) => {
  const styles = {
    draft: 'badge-saas-gray',
    submitted: 'badge-saas-blue border-blue-200 dark:border-blue-900/30',
    pending_approval: 'badge-saas-yellow border-yellow-200 dark:border-yellow-900/30',
    approved: 'badge-saas-green border-green-200 dark:border-green-900/30',
    paid: 'badge-saas-green font-bold border-green-300 dark:border-green-800/40',
    rejected: 'badge-saas-red border-red-200 dark:border-red-900/30',
    cancelled: 'badge-saas-gray',
  };

  const icons = {
    draft: <FileText size={12} />,
    submitted: <ArrowRight size={12} />,
    pending_approval: <Clock size={12} />,
    approved: <CheckCircle size={12} />,
    paid: <CheckCircle size={12} />,
    rejected: <XCircle size={12} />,
    cancelled: <AlertCircle size={12} />,
  };

  return (
    <span className={`badge-saas border gap-1.5 px-2.5 py-0.5 ${styles[status] || styles.draft}`}>
      {icons[status]}
      <span>{status.replace('_', ' ').toUpperCase()}</span>
    </span>
  );
};

const Invoices = ({ refreshTrigger }) => {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [submittingId, setSubmittingId] = useState(null);
  const [uploadDrawerOpen, setUploadDrawerOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const data = await getInvoices(params);
      setInvoices(Array.isArray(data) ? data : data.invoices || []);
    } catch (error) {
      console.error('Failed to fetch invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, [statusFilter, refreshTrigger]);

  const handleSubmit = async (id) => {
    setSubmittingId(id);
    try {
      await submitInvoice(id);
      fetchInvoices();
    } catch (error) {
      alert('Failed to submit invoice: ' + (error.response?.data?.error || error.message));
    } finally {
      setSubmittingId(null);
    }
  };

  // Filter local list based on client-side search query
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
          <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <FileText className="text-blue-600 dark:text-blue-400" /> Vendor Bills
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Accounts Payable invoices ingested via OCR and matching rules
          </p>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            onClick={() => setUploadDrawerOpen(true)}
            className="btn-primary flex-1 sm:flex-initial py-2 text-xs flex items-center justify-center gap-1.5"
          >
            <Upload size={14} />
            <span>Upload New Bill</span>
          </button>
          <button
            onClick={fetchInvoices}
            className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-500 hover:text-slate-900 dark:hover:text-slate-100"
            title="Refresh List"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
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
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Filter Status */}
        <div className="w-full md:w-48 relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" size={14} />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input-field pl-9 pr-8 text-xs appearance-none cursor-pointer"
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="submitted">Submitted</option>
            <option value="pending_approval">Pending Approval</option>
            <option value="approved">Approved</option>
            <option value="paid">Paid</option>
            <option value="rejected">Rejected</option>
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-400" />
        </div>
      </div>

      {/* Main Table Grid */}
      <div className="card-premium overflow-hidden bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
        {loading ? (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {[1, 2, 3, 4, 5].map((n) => (
              <div key={n} className="p-4 animate-pulse flex items-center justify-between">
                <div className="space-y-2 flex-1">
                  <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/3" />
                  <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-1/4" />
                </div>
                <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-16" />
                <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded w-20 ml-8" />
              </div>
            ))}
          </div>
        ) : filteredInvoices.length === 0 ? (
          <div className="p-16 text-center space-y-3">
            <div className="w-12 h-12 bg-slate-50 dark:bg-slate-800/50 rounded-full flex items-center justify-center text-slate-400 mx-auto border border-slate-100 dark:border-slate-800">
              <FileText size={20} />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No bills found</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                {searchQuery || statusFilter 
                  ? "Try adjusting your search criteria or status filter"
                  : "Get started by uploading a vendor bill or invoice."}
              </p>
            </div>
            {!searchQuery && !statusFilter && (
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
            <table className="table-saas">
              <thead>
                <tr>
                  <th>Vendor / Company</th>
                  <th>Bill Date</th>
                  <th>Segment / Category</th>
                  <th>Amount</th>
                  <th>Workflow Status</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredInvoices.map((inv) => (
                  <tr key={inv.id || inv._id} className="group">
                    <td>
                      <div className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                        <span>{inv.company || 'Unknown Vendor'}</span>
                        {inv.invoice_number && (
                          <span className="text-[10px] text-slate-400 font-mono bg-slate-50 dark:bg-slate-950 px-1 py-0.5 rounded border border-slate-100 dark:border-slate-800">
                            #{inv.invoice_number}
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">
                        Submitter: {inv.submitter_id ? `User ID ${inv.submitter_id.slice(-6)}` : 'System Ingestion'}
                      </div>
                    </td>
                    <td className="text-slate-500 dark:text-slate-400 font-mono text-xs">{inv.date || 'Pending Extraction'}</td>
                    <td>
                      <span className={`badge-saas uppercase text-[9px] ${
                        inv.category?.toLowerCase() === 'software' ? 'badge-saas-blue' :
                        inv.category?.toLowerCase() === 'supplies' ? 'badge-saas-green' :
                        inv.category?.toLowerCase() === 'food' ? 'badge-saas-yellow' : 'badge-saas-gray'
                      }`}>
                        {inv.category || 'Other'}
                      </span>
                    </td>
                    <td className="font-mono text-blue-600 dark:text-blue-400 font-bold">
                      ${(inv.total || 0).toFixed(2)}
                    </td>
                    <td>
                      <StatusBadge status={inv.status} />
                    </td>
                    <td className="text-right">
                      <div className="flex justify-end items-center gap-2">
                        <button 
                          onClick={() => setSelectedInvoice(inv)}
                          className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
                          title="View Details"
                        >
                          <ChevronRight size={16} />
                        </button>
                        {['draft', 'rejected'].includes(inv.status) && (
                          <button
                            onClick={() => handleSubmit(inv.id || inv._id)}
                            disabled={submittingId === (inv.id || inv._id)}
                            className="btn-primary py-1.5 px-3 text-xs shadow-sm"
                          >
                            {submittingId === (inv.id || inv._id) ? 'Sending...' : 'Submit Approval'}
                          </button>
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

      {/* Slide-over Drawer for Upload */}
      <AnimatePresence>
        {uploadDrawerOpen && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black z-50"
              onClick={() => setUploadDrawerOpen(false)}
            />
            <motion.div 
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'tween', duration: 0.25 }}
              className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl z-50 p-6 flex flex-col justify-between overflow-y-auto"
            >
              <div>
                <div className="flex justify-between items-center mb-6">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Ingest Document</span>
                  <button 
                    onClick={() => setUploadDrawerOpen(false)}
                    className="p-1 rounded-md text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                  >
                    <X size={16} />
                  </button>
                </div>
                <UploadInvoice onUploadSuccess={(data) => {
                  fetchInvoices();
                  setTimeout(() => setUploadDrawerOpen(false), 2000);
                }} />
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Invoice Details Dialog Modal */}
      <AnimatePresence>
        {selectedInvoice && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black z-50"
              onClick={() => setSelectedInvoice(null)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl z-50 p-6 overflow-hidden"
            >
              {/* Modal Header */}
              <div className="flex justify-between items-start pb-4 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                    Invoice Details
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Bill ID: {selectedInvoice.id || selectedInvoice._id}
                  </p>
                </div>
                <button 
                  onClick={() => setSelectedInvoice(null)}
                  className="p-1 rounded-md text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Modal Body */}
              <div className="py-4 space-y-4 max-h-[60vh] overflow-y-auto">
                <div className="grid grid-cols-2 gap-4">
                  {/* Vendor card */}
                  <div className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-850 rounded-xl space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold flex items-center gap-1"><Building size={12} /> Vendor</span>
                    <p className="text-sm font-bold text-slate-800 dark:text-slate-200">{selectedInvoice.company || 'N/A'}</p>
                    <p className="text-xs text-slate-500">No. {selectedInvoice.invoice_number || 'N/A'}</p>
                  </div>
                  {/* Status Card */}
                  <div className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-850 rounded-xl space-y-1.5">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold flex items-center gap-1"><Layers size={12} /> Status</span>
                    <div><StatusBadge status={selectedInvoice.status} /></div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {/* Date Card */}
                  <div className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-850 rounded-xl space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold flex items-center gap-1"><Calendar size={12} /> Invoice Date</span>
                    <p className="text-sm font-mono font-bold text-slate-800 dark:text-slate-200">{selectedInvoice.date || 'N/A'}</p>
                  </div>
                  {/* Category Card */}
                  <div className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-850 rounded-xl space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold flex items-center gap-1"><Layers size={12} /> Category Segment</span>
                    <p className="text-sm font-bold text-slate-800 dark:text-slate-200 capitalize">{selectedInvoice.category || 'N/A'}</p>
                  </div>
                </div>

                {/* Amount details */}
                <div className="p-4 border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 rounded-xl flex justify-between items-center">
                  <div>
                    <span className="text-xs text-slate-400">Grand Total Invoice Amount</span>
                    <p className="text-xs text-slate-500 mt-0.5">Calculated including matching tax elements</p>
                  </div>
                  <span className="text-xl font-mono font-bold text-blue-600 dark:text-blue-400">
                    ${(selectedInvoice.total || 0).toFixed(2)}
                  </span>
                </div>

                {/* AI Extracted parameters check list */}
                {selectedInvoice.extraction_results && (
                  <div className="space-y-2">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">AI Processing Logs</span>
                    <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-100 dark:border-slate-850 space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-500">OCR Read Status:</span>
                        <span className="font-semibold text-emerald-500">Success</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">AI Confidence:</span>
                        <span className="font-semibold text-blue-500">{(selectedInvoice.confidence || 0.95 * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-end gap-2">
                <button 
                  onClick={() => setSelectedInvoice(null)}
                  className="btn-secondary py-1.5 text-xs"
                >
                  Close View
                </button>
                {['draft', 'rejected'].includes(selectedInvoice.status) && (
                  <button
                    onClick={() => {
                      handleSubmit(selectedInvoice.id || selectedInvoice._id);
                      setSelectedInvoice(null);
                    }}
                    className="btn-primary py-1.5 text-xs"
                  >
                    Submit for Approval
                  </button>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

    </div>
  );
};

export default Invoices;
