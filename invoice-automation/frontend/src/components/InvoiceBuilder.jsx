import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, Save, Send, ChevronDown, ArrowLeft, FileText, Sparkles, Building, Layers, ShieldCheck, HelpCircle } from 'lucide-react';
import { getCustomers, getProducts, createARInvoice } from '../services/api';
import useToastStore from '../store/useToastStore';

const today = () => new Date().toISOString().split('T')[0];
const addDays = (n) => new Date(Date.now() + n * 86400000).toISOString().split('T')[0];

const EMPTY_LINE = { description: '', quantity: 1, unit_price: 0, tax_rate: 0 };

export default function InvoiceBuilder() {
  const navigate = useNavigate();
  const addToast = useToastStore(state => state.addToast);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const [header, setHeader] = useState({
    customer_id: '',
    issue_date: today(),
    due_date: addDays(30),
    currency: 'USD',
    notes: '',
    terms: 'Payment is due within 30 days of invoice date.',
    status: 'draft',
  });

  const [lines, setLines] = useState([{ ...EMPTY_LINE }]);
  const [discount, setDiscount] = useState(0);

  useEffect(() => {
    Promise.all([
      getCustomers({ limit: 200 }),
      getProducts({ limit: 200 }),
    ]).then(([cd, pd]) => {
      setCustomers(cd.customers || []);
      setProducts(pd.products || []);
    }).catch(() => setError('Failed to load customers or products. Check connection.'));
  }, []);

  // calculations
  const subtotal = lines.reduce((s, l) => s + Number(l.quantity) * Number(l.unit_price), 0);
  const taxTotal = lines.reduce(
    (s, l) => s + Number(l.quantity) * Number(l.unit_price) * (Number(l.tax_rate) / 100), 0
  );
  const grandTotal = subtotal + taxTotal - Number(discount);

  const setLine = (idx, field, value) => {
    setLines(ls => ls.map((l, i) => i === idx ? { ...l, [field]: value } : l));
  };

  const addLine = () => setLines(ls => [...ls, { ...EMPTY_LINE }]);
  const removeLine = (idx) => setLines(ls => ls.filter((_, i) => i !== idx));

  const fillFromProduct = (idx, productId) => {
    const p = products.find(p => p.id === productId);
    if (!p) return;
    setLines(ls => ls.map((l, i) => i === idx ? {
      ...l,
      description: p.name + (p.description ? ` — ${p.description}` : ''),
      unit_price: p.unit_price,
      tax_rate: p.tax_rate,
    } : l));
  };

  const handleSave = async (statusOverride) => {
    if (!header.customer_id) { setError('Please select a customer.'); return; }
    if (lines.length === 0 || lines.every(l => !l.description)) { setError('Add at least one line item.'); return; }

    setSaving(true);
    setError('');
    try {
      const payload = {
        ...header,
        status: statusOverride || header.status,
        line_items: lines.filter(l => l.description),
        discount: Number(discount),
      };
      await createARInvoice(payload);
      addToast(
        statusOverride === 'sent' 
          ? 'Invoice created and marked as sent.' 
          : 'Invoice saved as draft.',
        'success'
      );
      navigate('/ar/invoices');
    } catch (e) {
      addToast(e.response?.data?.error || 'Failed to create invoice.', 'error');
    } finally { setSaving(false); }
  };

  const selectedCustomer = customers.find(c => c.id === header.customer_id);

  return (
    <div className="space-y-6">
      
      {/* Top action bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => navigate('/ar/invoices')} 
            className="p-2 rounded-lg border border-slate-200 dark:border-slate-850 hover:bg-slate-100 dark:hover:bg-slate-900 text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <h1 className="text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
              <FileText className="text-blue-500" /> AR Invoice Builder
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Draft and issue client invoice logs, apply discounts, catalog items
            </p>
          </div>
        </div>

        <div className="flex gap-2 w-full sm:w-auto">
          <button 
            onClick={() => handleSave('draft')} 
            disabled={saving} 
            className="btn-secondary py-2 text-xs flex-1 sm:flex-initial flex items-center justify-center gap-1.5"
          >
            <Save size={14} />
            <span>Save Draft</span>
          </button>
          <button 
            onClick={() => handleSave('sent')} 
            disabled={saving} 
            className="btn-primary py-2 text-xs flex-1 sm:flex-initial flex items-center justify-center gap-1.5 shadow-md shadow-blue-500/10"
          >
            <Send size={14} />
            <span>{saving ? 'Processing...' : 'Issue & Send'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/50 rounded-xl p-4 text-rose-800 dark:text-rose-200 text-xs flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => setError('')} className="text-rose-500 hover:text-rose-700">✕</button>
        </div>
      )}

      {/* Main Form + Live Preview Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Form: Main Configuration */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Customer & Settings */}
          <div className="card-premium p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100 dark:border-slate-800 pb-2 flex items-center gap-1">
              <Building size={14} /> Customer Selection
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold uppercase text-slate-500 tracking-wider mb-1">
                  Customer Account *
                </label>
                <div className="relative">
                  <select
                    value={header.customer_id}
                    onChange={e => setHeader(h => ({ ...h, customer_id: e.target.value }))}
                    className="input-field pr-10 text-xs appearance-none cursor-pointer"
                  >
                    <option value="">— Select Customer —</option>
                    {customers.map(c => (
                      <option key={c.id} value={c.id}>{c.name} {c.email ? `(${c.email})` : ''}</option>
                    ))}
                  </select>
                  <div className="absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-400" />
                </div>
                {selectedCustomer && (
                  <div className="mt-2.5 p-3.5 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-150 dark:border-slate-850 text-xs text-slate-500 space-y-1">
                    <p className="font-semibold text-slate-800 dark:text-slate-200">{selectedCustomer.name}</p>
                    {selectedCustomer.billing_address && <p>📍 {selectedCustomer.billing_address}</p>}
                    {selectedCustomer.email && <p>✉️ {selectedCustomer.email}</p>}
                    <p>💳 Net Terms: {selectedCustomer.payment_terms || 'Net 30'}</p>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase text-slate-500 tracking-wider mb-1">
                    Issue Date
                  </label>
                  <input 
                    type="date" 
                    value={header.issue_date} 
                    onChange={e => setHeader(h => ({ ...h, issue_date: e.target.value }))}
                    className="input-field text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase text-slate-500 tracking-wider mb-1">
                    Due Date
                  </label>
                  <input 
                    type="date" 
                    value={header.due_date} 
                    onChange={e => setHeader(h => ({ ...h, due_date: e.target.value }))}
                    className="input-field text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase text-slate-500 tracking-wider mb-1">
                    Currency
                  </label>
                  <div className="relative">
                    <select
                      value={header.currency} 
                      onChange={e => setHeader(h => ({ ...h, currency: e.target.value }))}
                      className="input-field pr-10 text-xs appearance-none cursor-pointer"
                    >
                      {['USD','EUR','GBP','CAD','AUD','ETB'].map(c => <option key={c}>{c}</option>)}
                    </select>
                    <div className="absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-400" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Line items catalog */}
          <div className="card-premium p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                <Layers size={14} /> Line Items
              </h3>
              <button 
                onClick={addLine}
                className="text-xs text-blue-650 hover:underline inline-flex items-center gap-1 font-semibold"
              >
                <Plus size={14} />
                <span>Add Item</span>
              </button>
            </div>

            <div className="space-y-4">
              {lines.map((line, idx) => {
                const lineTotal = Number(line.quantity) * Number(line.unit_price) * (1 + Number(line.tax_rate) / 100);
                return (
                  <div 
                    key={idx} 
                    className="p-4 bg-slate-50/50 dark:bg-slate-950/30 border border-slate-150 dark:border-slate-850 rounded-xl space-y-3 relative group"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] font-bold text-slate-400">Row #{idx + 1}</span>
                      {lines.length > 1 && (
                        <button 
                          onClick={() => removeLine(idx)}
                          className="p-1 rounded text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/20"
                          title="Remove line"
                        >
                          <Trash2 size={13} />
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
                      {/* Product Selector / Custom description */}
                      <div className="sm:col-span-6 space-y-1.5">
                        {products.length > 0 && (
                          <div className="relative">
                            <select
                              value="" 
                              onChange={e => fillFromProduct(idx, e.target.value)}
                              className="input-field py-1 px-3 text-[10px] appearance-none cursor-pointer border-blue-200 dark:border-blue-900/35 text-blue-650"
                            >
                              <option value="">+ Pick from product catalog...</option>
                              {products.map(p => (
                                <option key={p.id} value={p.id}>{p.name} (${Number(p.unit_price).toFixed(2)})</option>
                              ))}
                            </select>
                            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-400" />
                          </div>
                        )}
                        <input
                          type="text"
                          placeholder="Description of item or service..."
                          value={line.description}
                          onChange={e => setLine(idx, 'description', e.target.value)}
                          className="input-field text-xs"
                          required
                        />
                      </div>

                      {/* Qty */}
                      <div className="sm:col-span-2">
                        <label className="block sm:hidden text-[9px] font-bold text-slate-400">Qty</label>
                        <input
                          type="number" 
                          min="1" 
                          step="1"
                          value={line.quantity} 
                          onChange={e => setLine(idx, 'quantity', e.target.value)}
                          className="input-field text-xs text-center"
                          placeholder="Qty"
                        />
                      </div>

                      {/* Price */}
                      <div className="sm:col-span-2">
                        <label className="block sm:hidden text-[9px] font-bold text-slate-400">Price</label>
                        <input
                          type="number" 
                          min="0" 
                          step="0.01"
                          value={line.unit_price} 
                          onChange={e => setLine(idx, 'unit_price', e.target.value)}
                          className="input-field text-xs font-mono text-right"
                          placeholder="0.00"
                        />
                      </div>

                      {/* Tax */}
                      <div className="sm:col-span-2 flex items-center justify-between gap-1.5">
                        <div className="flex-1">
                          <label className="block sm:hidden text-[9px] font-bold text-slate-400">Tax %</label>
                          <input
                            type="number" 
                            min="0" 
                            max="100" 
                            step="0.1"
                            value={line.tax_rate} 
                            onChange={e => setLine(idx, 'tax_rate', e.target.value)}
                            className="input-field text-xs font-mono text-right"
                            placeholder="Tax %"
                          />
                        </div>
                        <div className="text-right shrink-0 min-w-[50px] pt-1">
                          <span className="font-mono text-xs font-bold text-slate-700 dark:text-slate-350">
                            ${lineTotal.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <button 
              onClick={addLine}
              className="btn-secondary w-full py-2 text-xs flex items-center justify-center gap-1.5"
            >
              <Plus size={14} />
              <span>Add New Line Row</span>
            </button>
          </div>

          {/* Notes */}
          <div className="card-premium p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100 dark:border-slate-800 pb-2">
              Notes & Terms
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold uppercase text-slate-500 tracking-wider mb-1">
                  Customer Memo (visible on invoice PDF)
                </label>
                <textarea 
                  className="input-field text-xs min-h-[80px] resize-none"
                  value={header.notes} 
                  onChange={e => setHeader(h => ({ ...h, notes: e.target.value }))}
                  placeholder="Thank you for your business!"
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold uppercase text-slate-500 tracking-wider mb-1">
                  Terms & Conditions
                </label>
                <textarea 
                  className="input-field text-xs min-h-[80px] resize-none"
                  value={header.terms} 
                  onChange={e => setHeader(h => ({ ...h, terms: e.target.value }))}
                  placeholder="Payment is due within 30 days..."
                />
              </div>
            </div>
          </div>

        </div>

        {/* Right Preview Column */}
        <div className="space-y-6">
          
          {/* Invoice Summary Card */}
          <div className="card-premium p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 sticky top-24 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100 dark:border-slate-800 pb-2 flex items-center justify-between">
              <span>Financial Summary</span>
              <span className="text-[10px] bg-blue-50 dark:bg-slate-800 px-1.5 py-0.5 rounded text-blue-600 font-mono">
                {header.currency}
              </span>
            </h3>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between text-slate-500">
                <span>Subtotal</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-slate-500">
                <span>Cumulative Tax</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">${taxTotal.toFixed(2)}</span>
              </div>
              
              <div className="flex justify-between items-center text-slate-500">
                <span>Applied Discount</span>
                <div className="flex items-center gap-1.5 w-24">
                  <span className="text-slate-400">$</span>
                  <input
                    type="number" 
                    min="0" 
                    step="0.01"
                    className="input-field py-1 px-2 text-center text-xs font-mono"
                    value={discount}
                    onChange={e => setDiscount(e.target.value)}
                  />
                </div>
              </div>

              <div className="border-t border-slate-100 dark:border-slate-800 pt-3 flex justify-between items-baseline">
                <span className="font-bold text-slate-700 dark:text-slate-300">Total Due</span>
                <span className="text-xl font-bold font-mono text-blue-600 dark:text-blue-400">
                  ${grandTotal.toFixed(2)}
                </span>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2">
              <div>
                <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">
                  Submission Status
                </label>
                <div className="relative">
                  <select 
                    value={header.status} 
                    onChange={e => setHeader(h => ({ ...h, status: e.target.value }))}
                    className="input-field py-1.5 px-3 text-xs appearance-none cursor-pointer"
                  >
                    <option value="draft">Draft (Save only)</option>
                    <option value="sent">Sent (Active invoice)</option>
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-400" />
                </div>
              </div>
            </div>

            {/* Quick checklist */}
            <div className="pt-3.5 border-t border-slate-100 dark:border-slate-800 space-y-2 text-[10px] text-slate-500">
              <div className="flex items-center gap-1.5">
                <ShieldCheck size={14} className="text-emerald-500" />
                <span>Default tax calculations matches client profiles.</span>
              </div>
              <div className="flex items-center gap-1.5">
                <ShieldCheck size={14} className="text-emerald-500" />
                <span>Audited invoices are saved to local database.</span>
              </div>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
