import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  CheckSquare, 
  Users,
  Package,
  UserCircle,
  Settings,
  LogOut,
  Receipt,
  FileOutput,
  ShoppingBag,
  Scale
} from 'lucide-react';
import { cn } from '../../utils/cn';
import useAuthStore from '../../store/useAuthStore';

export function Sidebar({ onNavigate }) {
  const user = useAuthStore(state => state.user);
  const logout = useAuthStore(state => state.logout);

  const roles = user?.roles || ['viewer'];
  const isAdmin = roles.includes('admin');
  const isApprover = roles.includes('approver') || isAdmin;
  const isViewerOnly = roles.length === 1 && roles[0] === 'viewer';

  const navigation = [
    {
      section: 'Overview',
      items: [
        { name: 'Dashboard', to: '/', icon: LayoutDashboard },
      ]
    },
    {
      section: 'Accounts Payable',
      items: [
        { name: 'Invoices', to: '/ap/invoices', icon: FileText },
        ...(isApprover ? [{ name: 'Approvals', to: '/ap/approvals', icon: CheckSquare }] : []),
        { name: 'Purchase Orders', to: '/ap/purchase-orders', icon: ShoppingBag },
        { name: 'Vendors', to: '/ap/vendors', icon: Users },
      ]
    },
    {
      section: 'Accounts Receivable',
      items: [
        { name: 'AR Invoices', to: '/ar/invoices', icon: Receipt },
        ...(!isViewerOnly ? [{ name: 'Invoice Builder', to: '/ar/invoices/new', icon: FileOutput }] : []),
      ]
    },
    {
      section: 'Financial Records',
      items: [
        { name: 'Reconciliation & Exports', to: '/accounting/reconciliation', icon: Scale },
        { name: 'Customers', to: '/customers', icon: UserCircle },
        { name: 'Products', to: '/products', icon: Package },
      ]
    },
    ...(isAdmin ? [{
      section: 'Settings',
      items: [
        { name: 'Company Profile', to: '/settings/company', icon: Settings },
      ]
    }] : [])
  ];

  return (
    <aside className="w-full h-full bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-800 flex flex-col select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-neutral-200 dark:border-neutral-800 shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-sky-500 flex items-center justify-center shrink-0 shadow-sm">
            <FileText className="w-5 h-5 text-white" />
          </div>
          <div className="min-w-0">
            <h1 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-sky-500 bg-clip-text text-transparent truncate">
              InvoiceFlow
            </h1>
            <p className="text-[10px] text-neutral-400 capitalize truncate">
              {roles[0] || 'Member'} workspace
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-6">
        {navigation.map((section, idx) => (
          <div key={idx} className="space-y-1">
            <h3 className="px-3 text-[10px] font-bold text-neutral-400 dark:text-neutral-500 uppercase tracking-wider mb-1.5">
              {section.section}
            </h3>
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={() => onNavigate && onNavigate()}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-150',
                    isActive
                      ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-semibold shadow-xs'
                      : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-neutral-100'
                  )
                }
              >
                <item.icon className="w-4 h-4 shrink-0" />
                <span className="truncate">{item.name}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* User profile & Logout */}
      <div className="p-3 border-t border-neutral-200 dark:border-neutral-800 shrink-0 bg-neutral-50/50 dark:bg-neutral-900/50">
        <button
          onClick={() => {
            if (onNavigate) onNavigate();
            logout();
          }}
          className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-neutral-600 dark:text-neutral-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 hover:text-rose-600 dark:hover:text-rose-400 w-full transition-colors"
        >
          <LogOut className="w-4 h-4 shrink-0" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
