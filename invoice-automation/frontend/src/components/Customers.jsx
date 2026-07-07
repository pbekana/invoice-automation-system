import React, { useState, useEffect } from 'react';
import { Users, Plus, Search, Edit2, Trash2, X, Check, Mail, Phone, MapPin, DollarSign, Calendar, AlertCircle } from 'lucide-react';
import { getCustomers, createCustomer, updateCustomer, deleteCustomer } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import useToastStore from '../store/useToastStore';

const EMPTY_FORM = { name: '', email: '', phone: '', billing_address: '', shipping_address: '', currency: 'USD', payment_terms: 'Net 30', notes: '' };

const Modal = ({ title, onClose, children }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden"
    >
      <div className="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-800">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-white">{title}</h3>
        <button onClick={onClose} className="p-1 rounded-md text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800"><X size={16} /></button>
      </div>
      <div className="p-5">{children}</div>
    </motion.div>
  </div>
);

const CustomerForm = ({ initial = EMPTY_FORM, onSubmit, onClose, loading }) => {
  const [form, setForm] = useState(initial);
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));
  
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(form); }} className="space-y-4">
      <div>
        <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Company / Name *</label>
        <input 
          className="input-field text-xs" 
          value={form.name} 
          onChange={set('name')} 
          placeholder="Client Enterprises LLC" 
          required 
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Email</label>
          <input 
            className="input-field text-xs" 
            type="email" 
            value={form.email} 
            onChange={set('email')} 
            placeholder="finance@client.com" 
          />
        </div>
        <div>
          <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Phone</label>
          <input 
            className="input-field text-xs" 
            value={form.phone} 
            onChange={set('phone')} 
            placeholder="+1 555-0199" 
          />
        </div>
      </div>

      <div>
        <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Billing Address</label>
        <input 
          className="input-field text-xs" 
          value={form.billing_address} 
          onChange={set('billing_address')} 
          placeholder="Building 40, Technology Park" 
        />
      </div>

      <div>
        <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Shipping Address</label>
        <input 
          className="input-field text-xs" 
          value={form.shipping_address} 
          onChange={set('shipping_address')} 
          placeholder="Same as billing (Optional)" 
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Currency</label>
          <div className="relative">
            <select 
              className="input-field pr-10 text-xs appearance-none cursor-pointer" 
              value={form.currency} 
              onChange={set('currency')}
            >
              {['USD','EUR','GBP','CAD','AUD','ETB'].map(c => <option key={c}>{c}</option>)}
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-400" />
          </div>
        </div>
        <div>
          <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Payment Terms</label>
          <div className="relative">
            <select 
              className="input-field pr-10 text-xs appearance-none cursor-pointer" 
              value={form.payment_terms} 
              onChange={set('payment_terms')}
            >
              {['Due on Receipt','Net 7','Net 15','Net 30','Net 60'].map(t => <option key={t}>{t}</option>)}
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-400" />
          </div>
        </div>
      </div>

      <div>
        <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Memo / Notes</label>
        <input 
          className="input-field text-xs" 
          value={form.notes} 
          onChange={set('notes')} 
          placeholder="Internal reference details..." 
        />
      </div>

      <div className="flex gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
        <button 
          type="button" 
          onClick={onClose} 
          className="flex-1 btn-secondary py-2 text-xs"
        >
          Cancel
        </button>
        <button 
          type="submit" 
          disabled={loading} 
          className="flex-1 btn-primary py-2 text-xs"
        >
          {loading ? 'Saving...' : 'Save Customer'}
        </button>
      </div>
    </form>
  );
};

const StatusBadge = ({ status }) => {
  const colors = { 
    active: 'badge-saas-green', 
    inactive: 'badge-saas-red' 
  };
  return (
    <span className={`badge-saas text-[9px] uppercase ${colors[status] || colors.active}`}>
      {status || 'active'}
    </span>
  );
};

export default function Customers() {
  const addToast = useToastStore(state => state.addToast);
  const [customers, setCustomers] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [modal, setModal] = useState(null); // null | 'create' | { ...customer }
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const data = await getCustomers({ search });
      setCustomers(data.customers || []);
      setTotalCount(data.total || 0);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch client list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      load();
    }, 300);
    return () => clearTimeout(delayDebounce);
  }, [search]);

  const handleCreate = async (form) => {
    setSaving(true);
    try {
      await createCustomer(form);
      setModal(null);
      addToast('Customer account created successfully.', 'success');
      load();
    } catch (e) {
      addToast(e.response?.data?.error || 'Failed to create customer', 'error');
    } finally { setSaving(false); }
  };

  const handleUpdate = async (form) => {
    setSaving(true);
    try {
      await updateCustomer(modal.id, form);
      setModal(null);
      addToast('Customer profile updated.', 'success');
      load();
    } catch (e) {
      addToast(e.response?.data?.error || 'Failed to update customer', 'error');
    } finally { setSaving(false); }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Are you sure you want to deactivate customer "${name}"?`)) return;
    try {
      await deleteCustomer(id);
      addToast(`"${name}" has been deactivated.`, 'info');
      load();
    } catch (err) { 
      addToast('Failed to deactivate customer account.', 'error');
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <Users className="text-blue-500" /> Customers
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {totalCount} total corporate accounts registered
          </p>
        </div>
        <button 
          onClick={() => setModal('create')} 
          className="btn-primary py-2 text-xs flex items-center gap-1.5 shadow-md shadow-blue-500/10"
        >
          <Plus size={14} />
          <span>Add New Customer</span>
        </button>
      </div>

      {error && (
        <div className="bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/50 rounded-xl p-4 text-rose-800 dark:text-rose-200 text-xs flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => setError('')} className="p-1 rounded hover:bg-rose-100 dark:hover:bg-rose-950/40">✕</button>
        </div>
      )}

      {/* Search Input */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input 
          className="input-field pl-9 text-xs" 
          placeholder="Search by company name, contact, or email address..." 
          value={search} 
          onChange={e => setSearch(e.target.value)} 
        />
      </div>

      {/* Directory Content Table */}
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
        ) : customers.length === 0 ? (
          <div className="p-16 text-center space-y-4">
            <div className="w-12 h-12 bg-slate-50 dark:bg-slate-850 rounded-full flex items-center justify-center text-slate-400 mx-auto border border-slate-100 dark:border-slate-850">
              <Users size={20} />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-350">No customers registered</p>
              <p className="text-xs text-slate-500 mt-1">
                Add corporate accounts to issue client invoices.
              </p>
            </div>
            <button 
              onClick={() => setModal('create')} 
              className="btn-secondary py-1.5 text-xs inline-flex items-center gap-1 mx-auto"
            >
              <Plus size={12} />
              <span>Create client profile</span>
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-saas">
              <thead>
                <tr>
                  <th>Client / Corporate Account</th>
                  <th>Primary Billing Contact</th>
                  <th>Preferred Currency</th>
                  <th>Terms</th>
                  <th>Account Status</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {customers.map(c => (
                  <tr key={c.id || c._id} className="group">
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-950/30 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-xs border border-blue-100 dark:border-blue-900/30">
                          {c.name[0].toUpperCase()}
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900 dark:text-white text-xs">{c.name}</div>
                          {c.billing_address && (
                            <div className="text-slate-400 dark:text-slate-500 text-[10px] flex items-center gap-1 mt-0.5">
                              <MapPin size={10} />
                              <span className="truncate max-w-[180px]">{c.billing_address}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td>
                      {c.email && (
                        <div className="text-slate-600 dark:text-slate-300 text-xs flex items-center gap-1 font-mono">
                          <Mail size={12} className="text-slate-400" />
                          <span>{c.email}</span>
                        </div>
                      )}
                      {c.phone && (
                        <div className="text-slate-400 dark:text-slate-500 text-[10px] flex items-center gap-1 mt-0.5">
                          <Phone size={10} />
                          <span>{c.phone}</span>
                        </div>
                      )}
                    </td>
                    <td>
                      <span className="text-slate-700 dark:text-slate-300 text-xs font-mono font-bold">{c.currency || 'USD'}</span>
                    </td>
                    <td>
                      <span className="text-slate-600 dark:text-slate-400 text-xs font-medium">{c.payment_terms || 'Net 30'}</span>
                    </td>
                    <td>
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="text-right">
                      <div className="flex items-center gap-2 justify-end">
                        <button 
                          onClick={() => setModal(c)} 
                          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                          title="Edit Customer"
                        >
                          <Edit2 size={13} />
                        </button>
                        <button 
                          onClick={() => handleDelete(c.id || c._id, c.name)} 
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-colors"
                          title="Deactivate Customer"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modals Form Render */}
      <AnimatePresence>
        {modal && (
          <Modal 
            title={modal === 'create' ? "New Customer Profile" : "Edit Customer Profile"} 
            onClose={() => setModal(null)}
          >
            <CustomerForm 
              initial={modal === 'create' ? EMPTY_FORM : modal} 
              onSubmit={modal === 'create' ? handleCreate : handleUpdate} 
              onClose={() => setModal(null)} 
              loading={saving} 
            />
          </Modal>
        )}
      </AnimatePresence>

    </div>
  );
}
