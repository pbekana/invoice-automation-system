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
  FileOutput
} from 'lucide-react';
import { cn } from '../../utils/cn';
import useAuthStore from '../../store/useAuthStore';

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
      { name: 'Approvals', to: '/ap/approvals', icon: CheckSquare },
      { name: 'Vendors', to: '/ap/vendors', icon: Users },
    ]
  },
  {
    section: 'Accounts Receivable',
    items: [
      { name: 'AR Invoices', to: '/ar/invoices', icon: Receipt },
      { name: 'Invoice Builder', to: '/ar/invoices/new', icon: FileOutput },
    ]
  },
  {
    section: 'Management',
    items: [
      { name: 'Customers', to: '/customers', icon: UserCircle },
      { name: 'Products', to: '/products', icon: Package },
    ]
  },
  {
    section: 'Settings',
    items: [
      { name: 'Company Profile', to: '/settings/company', icon: Settings },
    ]
  },
];

export function Sidebar() {
  const logout = useAuthStore(state => state.logout);

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-800 flex flex-col z-30">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-neutral-200 dark:border-neutral-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-600 to-brand-400 flex items-center justify-center">
            <FileText className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-brand-600 to-brand-400 bg-clip-text text-transparent">
            InvoiceFlow
          </h1>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto">
        {navigation.map((section, idx) => (
          <div key={idx} className="mb-6">
            <h3 className="px-3 text-xs font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider mb-2">
              {section.section}
            </h3>
            <div className="space-y-1">
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                      isActive
                        ? 'bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-400'
                        : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-neutral-100'
                    )
                  }
                >
                  <item.icon className="w-5 h-5 flex-shrink-0" />
                  <span>{item.name}</span>
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Logout */}
      <div className="p-3 border-t border-neutral-200 dark:border-neutral-800">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-neutral-100 w-full transition-colors"
        >
          <LogOut className="w-5 h-5" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
