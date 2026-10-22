import React, { useState, useEffect, useCallback } from 'react';
import { 
  ShoppingBag, 
  Plus, 
  Search, 
  RefreshCw, 
  CheckCircle2, 
  AlertTriangle, 
  X, 
  Layers, 
  Building, 
  Percent, 
  DollarSign,
  FileText
} from 'lucide-react';
import { getPurchaseOrders, createPurchaseOrder } from '../services/api';
import useToastStore from '../store/useToastStore';
import useAuthStore from '../store/useAuthStore';

export default function PurchaseOrders() {
  const addToast = useToastStore(state => state.addToast);
  const user = useAuthStore(state => state.user);
  const [pos, setPos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [search, setSearch] = useState('');

  const [form, setForm] = useState({
    po_number: '',
    vendor_name: '',
    total_amount: '',
    tolerance_percent: 5.0,
    notes: '',
  });

  const roles = user?.roles || [];
  const canCreate = roles.includes('admin') || roles.includes('approver') || roles.includes('submitter');

  const fetchPOs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getPurchaseOrders();
      setPos(res.purchase_orders || []);
    } catch {
      addToast('Failed to load purchase orders.', 'error');
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchPOs();
  }, [fetchPOs]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.po_number || !form.vendor_name || !form.total_amount) {
      addToast('Please fill all required fields.', 'error');
      return;
    }

    try {
      await createPurchaseOrder({
        ...form,
        total_amount: parseFloat(form.total_amount),
        tolerance_percent: parseFloat(form.tolerance_percent || 5.0)
      });
      addToast(`Purchase Order ${form.po_number} created successfully.`, 'success');
      setModalOpen(false);
      setForm({ po_number: '', vendor_name: '', total_amount: '', tolerance_percent: 5.0, notes: '' });
      fetchPOs();
    } catch (err) {
      addToast(err.response?.data?.error || 'Failed to create PO.', 'error');
    }
  };

  const filtered = pos.filter(p => {
    const q = search.toLowerCase();
    return (p.po_number || '').toLowerCase().includes(q) || (p.vendor_name || '').toLowerCase().includes(q);
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-neutral-900 dark:text-white flex items-center gap-2">
            <ShoppingBag className="text-blue-600 dark:text-blue-400" />
            Purchase Orders & Matching
          </h1>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
            Registered procurement commitments for automated 2-way and 3-way variance verification.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {canCreate && (
            <button
              onClick={() => setModalOpen(true)}
              className="btn-primary py-2 px-3 text-xs flex items-center gap-1.5"
            >
              <Plus size={14} />
              <span>Create Purchase Order</span>
            </button>
          )}
          <button
            onClick={fetchPOs}
            className="p-2 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 text-neutral-500 hover:text-neutral-900"
            title="Refresh"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
        <input
          type="text"
          placeholder="Search by PO number or vendor..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field pl-9 text-xs"
        />
      </div>

      {/* PO Table Card */}
      <div className="card-premium overflow-hidden bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800">
        {loading ? (
          <div className="p-8 text-center text-xs text-neutral-400">Loading purchase orders...</div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <ShoppingBag size={24} className="mx-auto text-neutral-400" />
            <p className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">No Purchase Orders Found</p>
            <p className="text-xs text-neutral-500">Create a purchase order to enable automated matching against uploaded bills.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-saas min-w-[650px]">
              <thead>
                <tr>
                  <th>PO Reference</th>
                  <th>Vendor / Supplier</th>
                  <th>Authorized Total</th>
                  <th>Allowed Variance</th>
                  <th>Procurement Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((po) => (
                  <tr key={po.id || po._id}>
                    <td>
                      <div className="font-mono text-xs font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-1.5">
                        <FileText size={13} className="text-blue-500 shrink-0" />
                        <span>{po.po_number}</span>
                      </div>
                      <div className="text-[10px] text-neutral-400 mt-0.5">{po.currency || 'USD'}</div>
                    </td>
                    <td>
                      <div className="text-xs font-semibold text-neutral-800 dark:text-neutral-200 flex items-center gap-1.5">
                        <Building size={13} className="text-neutral-400 shrink-0" />
                        <span>{po.vendor_name}</span>
                      </div>
                    </td>
                    <td className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400">
                      ${(po.total_amount || 0).toFixed(2)}
                    </td>
                    <td className="text-xs font-mono text-neutral-600 dark:text-neutral-400">
                      ±{po.tolerance_percent || 5}%
                    </td>
                    <td>
                      <span className="badge-saas badge-saas-green uppercase text-[10px] font-bold">
                        {po.status || 'open'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal for Creating PO */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden p-6 space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-neutral-100 dark:border-neutral-800">
              <h3 className="text-sm font-bold uppercase tracking-wider text-neutral-800 dark:text-white">
                New Purchase Order
              </h3>
              <button onClick={() => setModalOpen(false)} className="text-neutral-400 hover:text-neutral-600">
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-[10px] font-bold uppercase text-neutral-500 mb-1">
                  PO Number *
                </label>
                <input
                  type="text"
                  required
                  placeholder="PO-2026-0042"
                  value={form.po_number}
                  onChange={(e) => setForm({ ...form, po_number: e.target.value })}
                  className="input-field text-xs font-mono"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase text-neutral-500 mb-1">
                  Vendor Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="AWS, Office Depot, etc."
                  value={form.vendor_name}
                  onChange={(e) => setForm({ ...form, vendor_name: e.target.value })}
                  className="input-field text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-bold uppercase text-neutral-500 mb-1">
                    Total Amount ($) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="1500.00"
                    value={form.total_amount}
                    onChange={(e) => setForm({ ...form, total_amount: e.target.value })}
                    className="input-field text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase text-neutral-500 mb-1">
                    Variance Tol. (%)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    placeholder="5.0"
                    value={form.tolerance_percent}
                    onChange={(e) => setForm({ ...form, tolerance_percent: e.target.value })}
                    className="input-field text-xs font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase text-neutral-500 mb-1">
                  Notes / Procurement Spec
                </label>
                <textarea
                  rows={2}
                  placeholder="Authorized recurring supply order"
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  className="input-field text-xs"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-neutral-100 dark:border-neutral-800">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="btn-secondary py-1.5 px-3 text-xs"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary py-1.5 px-3 text-xs">
                  Save Purchase Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
