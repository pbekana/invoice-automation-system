import React, { useState, useEffect } from 'react';
import { Box, Plus, Search, Edit2, Trash2, X, Tag, DollarSign, Percent, AlertCircle } from 'lucide-react';
import { getProducts, createProduct, updateProduct, deleteProduct } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import useToastStore from '../store/useToastStore';

const EMPTY = { name: '', sku: '', description: '', unit_price: '', tax_rate: '', category: '' };

const Modal = ({ title, onClose, children }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden"
    >
      <div className="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-800">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-white">{title}</h3>
        <button onClick={onClose} className="p-1 rounded-md text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800"><X size={16} /></button>
      </div>
      <div className="p-5">{children}</div>
    </motion.div>
  </div>
);

const ProductForm = ({ initial = EMPTY, onSubmit, onClose, loading }) => {
  const [form, setForm] = useState(initial);
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(form); }} className="space-y-4">
      <div>
        <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Product / Service Name *</label>
        <input 
          className="input-field text-xs" 
          value={form.name} 
          onChange={set('name')} 
          placeholder="Professional Consulting" 
          required 
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">SKU / Code</label>
          <input 
            className="input-field text-xs font-mono" 
            value={form.sku} 
            onChange={set('sku')} 
            placeholder="SRV-CON-01" 
          />
        </div>
        <div>
          <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Category</label>
          <input 
            className="input-field text-xs" 
            value={form.category} 
            onChange={set('category')} 
            placeholder="Consulting" 
          />
        </div>
      </div>

      <div>
        <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Description</label>
        <input 
          className="input-field text-xs" 
          value={form.description} 
          onChange={set('description')} 
          placeholder="Optional service details..." 
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Unit Price ($)</label>
          <div className="relative">
            <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={14} />
            <input 
              className="input-field pl-8 text-xs font-mono" 
              type="number" 
              step="0.01" 
              min="0" 
              value={form.unit_price} 
              onChange={set('unit_price')} 
              placeholder="0.00" 
            />
          </div>
        </div>
        <div>
          <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">Tax Rate (%)</label>
          <div className="relative">
            <Percent className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={14} />
            <input 
              className="input-field pl-8 text-xs font-mono" 
              type="number" 
              step="0.01" 
              min="0" 
              max="100" 
              value={form.tax_rate} 
              onChange={set('tax_rate')} 
              placeholder="0.00" 
            />
          </div>
        </div>
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
          {loading ? 'Saving...' : 'Save Product'}
        </button>
      </div>
    </form>
  );
};

export default function Products() {
  const addToast = useToastStore(state => state.addToast);
  const [products, setProducts] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [modal, setModal] = useState(null);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const data = await getProducts({ search });
      setProducts(data.products || []);
      setTotalCount(data.total || 0);
    } catch (err) { 
      console.error(err);
      setError('Failed to fetch item catalog.'); 
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
      await createProduct(form); 
      setModal(null);
      addToast('Product added to catalog.', 'success');
      load(); 
    } catch (e) { 
      addToast(e.response?.data?.error || 'Failed to create product', 'error');
    } finally { 
      setSaving(false); 
    }
  };

  const handleUpdate = async (form) => {
    setSaving(true);
    try { 
      await updateProduct(modal.id, form); 
      setModal(null);
      addToast('Product catalog item updated.', 'success');
      load(); 
    } catch (e) { 
      addToast(e.response?.data?.error || 'Failed to update product', 'error');
    } finally { 
      setSaving(false); 
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Are you sure you want to deactivate item "${name}"?`)) return;
    try { 
      await deleteProduct(id);
      addToast(`"${name}" removed from catalog.`, 'info');
      load(); 
    } catch (err) { 
      addToast('Failed to deactivate product item.', 'error');
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <Box className="text-blue-500" /> Products & Services
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {totalCount} active items in client catalog
          </p>
        </div>
        <button 
          onClick={() => setModal('create')} 
          className="btn-primary py-2 text-xs flex items-center gap-1.5 shadow-md shadow-blue-500/10"
        >
          <Plus size={14} />
          <span>Add Catalog Item</span>
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
          placeholder="Search items by name, category, or SKU code..." 
          value={search} 
          onChange={e => setSearch(e.target.value)} 
        />
      </div>

      {/* Content Table Grid */}
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
        ) : products.length === 0 ? (
          <div className="p-16 text-center space-y-4">
            <div className="w-12 h-12 bg-slate-50 dark:bg-slate-850 rounded-full flex items-center justify-center text-slate-400 mx-auto border border-slate-100 dark:border-slate-850">
              <Box size={20} />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-350">No products registered</p>
              <p className="text-xs text-slate-550 mt-1">
                Add catalog items to include them as default options in AR builder.
              </p>
            </div>
            <button 
              onClick={() => setModal('create')} 
              className="btn-secondary py-1.5 text-xs inline-flex items-center gap-1 mx-auto"
            >
              <Plus size={12} />
              <span>Create catalog item</span>
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-saas">
              <thead>
                <tr>
                  <th>Product / Service</th>
                  <th>SKU / Code</th>
                  <th>Default Category</th>
                  <th>Unit Price</th>
                  <th>Default Tax</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map(p => (
                  <tr key={p.id || p._id} className="group">
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-950/30 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-xs border border-blue-100 dark:border-blue-900/30">
                          <Box size={14} />
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900 dark:text-white text-xs">{p.name}</div>
                          {p.description && (
                            <div className="text-slate-400 dark:text-slate-500 text-[10px] mt-0.5 max-w-xs truncate">
                              {p.description}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="text-slate-400 dark:text-slate-500 font-mono text-xs font-semibold">
                        {p.sku || '—'}
                      </span>
                    </td>
                    <td>
                      {p.category ? (
                        <span className="badge-saas text-[9px] uppercase badge-saas-gray inline-flex items-center gap-1">
                          <Tag size={10} />
                          <span>{p.category}</span>
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs">—</span>
                      )}
                    </td>
                    <td>
                      <span className="text-slate-900 dark:text-white font-mono font-bold text-xs">
                        ${Number(p.unit_price || 0).toFixed(2)}
                      </span>
                    </td>
                    <td>
                      <span className="text-slate-500 dark:text-slate-400 text-xs font-mono">
                        {p.tax_rate || 0}%
                      </span>
                    </td>
                    <td className="text-right">
                      <div className="flex items-center gap-2 justify-end">
                        <button 
                          onClick={() => setModal(p)} 
                          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                          title="Edit Item"
                        >
                          <Edit2 size={13} />
                        </button>
                        <button 
                          onClick={() => handleDelete(p.id || p._id, p.name)} 
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-colors"
                          title="Deactivate Item"
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
            title={modal === 'create' ? "New Product / Service" : "Edit Product Catalog Item"} 
            onClose={() => setModal(null)}
          >
            <ProductForm 
              initial={modal === 'create' ? EMPTY : modal} 
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
