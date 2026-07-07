import React, { useState, useEffect } from 'react';
import { Settings, Save, Building2, Mail, Phone, MapPin, CreditCard, X, Check, Globe, HelpCircle, FileText } from 'lucide-react';
import { getCompany, saveCompany } from '../services/api';
import useToastStore from '../store/useToastStore';

const Input = ({ label, icon: Icon, ...props }) => (
  <div>
    <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1.5 tracking-wider">{label}</label>
    <div className="relative">
      {Icon && <Icon size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />}
      <input
        className={`input-field text-xs ${Icon ? 'pl-9 pr-4' : 'px-4'}`}
        {...props}
      />
    </div>
  </div>
);

const Section = ({ title, children }) => (
  <div className="card-premium p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 space-y-4">
    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800 pb-2">{title}</h3>
    {children}
  </div>
);

export default function CompanyProfile() {
  const addToast = useToastStore(state => state.addToast);
  const [form, setForm] = useState({
    name: '', email: '', phone: '', address: '', tax_id: '',
    currency: 'USD', invoice_prefix: 'INV-', payment_instructions: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getCompany();
        if (data.company) setForm(prev => ({ ...prev, ...data.company }));
      } catch { 
        setError('Failed to load company profile from server.'); 
      } finally { 
        setLoading(false); 
      }
    };
    load();
  }, []);

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await saveCompany(form);
      addToast('Company configuration saved successfully.', 'success');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save profile parameters');
    } finally { setSaving(false); }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-xs text-slate-400">Loading company profile settings...</div>
    </div>
  );

  return (
    <div className="space-y-6 max-w-3xl">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <Settings className="text-blue-500" /> Company Configuration
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Configure primary business address, standard tax IDs, payment terms, and defaults
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/50 rounded-xl p-4 text-rose-800 dark:text-rose-200 text-xs flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => setError('')} className="p-1 rounded hover:bg-rose-100"><X size={14} /></button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        
        <Section title="Business Info & Address">
          <Input label="Company Name *" icon={Building2} value={form.name} onChange={set('name')} placeholder="Acme Corporate Ltd." required />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Billing Contact Email" icon={Mail} type="email" value={form.email} onChange={set('email')} placeholder="finance@acme.com" />
            <Input label="Business Phone" icon={Phone} value={form.phone} onChange={set('phone')} placeholder="+1 555-0100" />
          </div>
          <Input label="Full Business Address" icon={MapPin} value={form.address} onChange={set('address')} placeholder="120 Technology Way, Suite 10, California" />
          <Input label="Tax ID / Registration Number" icon={FileText} value={form.tax_id} onChange={set('tax_id')} placeholder="EIN: XX-XXXXXXX" />
        </Section>

        <Section title="Default Billing Defaults">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1.5">Standard Currency</label>
              <div className="relative">
                <select 
                  className="input-field pr-10 text-xs appearance-none cursor-pointer" 
                  value={form.currency} 
                  onChange={set('currency')}
                >
                  {['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'ETB', 'JPY'].map(c => <option key={c}>{c}</option>)}
                </select>
                <div className="absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-400" />
              </div>
            </div>
            <Input label="Invoice Number Prefix" value={form.invoice_prefix} onChange={set('invoice_prefix')} placeholder="INV-" />
          </div>

          <div>
            <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1.5">Default Remittance Instructions</label>
            <textarea
              className="input-field text-xs min-h-[100px] resize-none"
              rows={4}
              value={form.payment_instructions}
              onChange={set('payment_instructions')}
              placeholder="Provide default payment routes, e.g. wire/ACH details, routing numbers..."
            />
            <p className="text-[10px] text-slate-400 mt-1">This text appears at the base of client-facing invoices.</p>
          </div>
        </Section>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="btn-primary py-2.5 px-6 text-xs flex items-center gap-1.5 shadow-md shadow-blue-500/10"
          >
            <Save size={14} />
            <span>{saving ? 'Saving...' : 'Save Configuration'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
