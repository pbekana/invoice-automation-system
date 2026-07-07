import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, XCircle, Info, AlertTriangle, X } from 'lucide-react';
import useToastStore from '../../store/useToastStore';

const ICONS = {
  success: <CheckCircle2 size={16} className="text-emerald-500 shrink-0" />,
  error: <XCircle size={16} className="text-rose-500 shrink-0" />,
  info: <Info size={16} className="text-blue-500 shrink-0" />,
  warning: <AlertTriangle size={16} className="text-amber-500 shrink-0" />,
};

const STYLES = {
  success: 'bg-white dark:bg-slate-900 border-emerald-200 dark:border-emerald-800/50',
  error:   'bg-white dark:bg-slate-900 border-rose-200 dark:border-rose-800/50',
  info:    'bg-white dark:bg-slate-900 border-blue-200 dark:border-blue-800/50',
  warning: 'bg-white dark:bg-slate-900 border-amber-200 dark:border-amber-800/50',
};

const TEXT_STYLES = {
  success: 'text-emerald-800 dark:text-emerald-200',
  error:   'text-rose-800 dark:text-rose-200',
  info:    'text-blue-800 dark:text-blue-200',
  warning: 'text-amber-800 dark:text-amber-200',
};

function Toast({ id, message, type = 'success' }) {
  const removeToast = useToastStore(state => state.removeToast);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -10, scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      className={`flex items-start gap-3 px-4 py-3 rounded-xl border shadow-lg max-w-sm w-full ${STYLES[type]}`}
    >
      {ICONS[type]}
      <p className={`text-xs font-medium flex-1 leading-relaxed ${TEXT_STYLES[type]}`}>
        {message}
      </p>
      <button
        onClick={() => removeToast(id)}
        className="shrink-0 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors p-0.5 rounded"
      >
        <X size={14} />
      </button>
    </motion.div>
  );
}

export default function ToastContainer() {
  const toasts = useToastStore(state => state.toasts);

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 items-end pointer-events-none">
      <AnimatePresence mode="sync">
        {toasts.map(toast => (
          <div key={toast.id} className="pointer-events-auto">
            <Toast {...toast} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
}
