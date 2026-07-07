import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import useAuthStore from '../../store/useAuthStore';
import useThemeStore from '../../store/useThemeStore';
import { 
  LayoutDashboard, 
  List, 
  CheckSquare, 
  Users, 
  LogOut, 
  FileText, 
  Settings,
  Building2,
  FilePlus,
  Box,
  Sun,
  Moon,
  Menu,
  X,
  Search,
  Bell,
  ChevronDown,
  User
} from 'lucide-react';
import { logoutUser } from '../../services/api';
import { motion, AnimatePresence } from 'framer-motion';

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore(state => state.logout);
  const user = useAuthStore(state => state.user) || JSON.parse(localStorage.getItem('user')) || { name: 'User', email: 'user@example.com' };
  
  const { theme, toggleTheme } = useThemeStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  // Close menus when page changes
  useEffect(() => {
    setMobileMenuOpen(false);
    setProfileMenuOpen(false);
    setNotificationsOpen(false);
  }, [location]);

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch(e) {
      console.error(e);
    }
    logout();
    navigate('/login');
  };

  const navItems = [
    { section: 'Overview' },
    { to: '/', icon: <LayoutDashboard size={18} />, label: 'Dashboard' },
    { section: 'Accounts Receivable' },
    { to: '/ar/invoices/new', icon: <FilePlus size={18} />, label: 'Create Invoice' },
    { to: '/ar/invoices', icon: <FileText size={18} />, label: 'Customer Invoices' },
    { to: '/customers', icon: <Users size={18} />, label: 'Customers' },
    { to: '/products', icon: <Box size={18} />, label: 'Products & Services' },
    { section: 'Accounts Payable' },
    { to: '/ap/invoices', icon: <List size={18} />, label: 'Vendor Bills' },
    { to: '/ap/approvals', icon: <CheckSquare size={18} />, label: 'Approvals' },
    { to: '/ap/vendors', icon: <Building2 size={18} />, label: 'Vendors' },
    { section: 'Settings' },
    { to: '/settings/company', icon: <Settings size={18} />, label: 'Company Profile' },
  ];

  // Get active page name for header
  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/') return 'Dashboard';
    if (path === '/ar/invoices/new') return 'Create AR Invoice';
    if (path === '/ar/invoices') return 'Accounts Receivable Invoices';
    if (path === '/customers') return 'Customer Management';
    if (path === '/products') return 'Product & Services Catalog';
    if (path === '/ap/invoices') return 'Accounts Payable Bills';
    if (path === '/ap/approvals') return 'Approval Workflow Queue';
    if (path === '/ap/vendors') return 'Vendor Profiles';
    if (path === '/settings/company') return 'Company Configuration';
    return 'Billing Engine';
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full bg-slate-900 border-r border-slate-800 text-slate-300">
      
      {/* Brand Header */}
      <div className="p-5 flex items-center gap-3 border-b border-slate-800 shrink-0">
        <div className="p-2 bg-blue-600 rounded-lg shadow-md shadow-blue-500/20">
          <FileText className="text-white" size={20} />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-white m-0">BillOrbit</h1>
          <p className="text-[10px] text-blue-400 font-bold uppercase tracking-widest leading-none mt-0.5">SaaS Edition</p>
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {navItems.map((item, idx) => {
          if (item.section) {
            return (
              <div key={idx} className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-5 mb-1 px-3">
                {item.section}
              </div>
            );
          }
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors font-medium text-sm ${
                  isActive
                    ? 'bg-blue-600/10 text-blue-400 border-l-2 border-blue-500 pl-2.5'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-100'
                }`
              }
            >
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Sidebar Footer User Info & Signout */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/50 shrink-0">
        <div className="flex items-center gap-3 mb-3 px-1">
          <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
            {user.name ? user.name[0].toUpperCase() : 'U'}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold text-white truncate leading-tight">{user.name || 'Admin User'}</p>
            <p className="text-[10px] text-slate-500 truncate mt-0.5">{user.email || 'admin@example.com'}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2.5 px-3 py-2 w-full rounded-lg text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-colors font-medium text-xs border border-transparent hover:border-red-500/20"
        >
          <LogOut size={16} />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans transition-colors duration-200">
      
      {/* Desktop Sidebar (hidden on mobile/tablet) */}
      <aside className="hidden lg:block w-64 shrink-0 h-full">
        <SidebarContent />
      </aside>

      {/* Mobile Drawer Slide-over Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-50 lg:hidden flex">
            {/* Backdrop */}
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black"
              onClick={() => setMobileMenuOpen(false)}
            />
            {/* Drawer */}
            <motion.div 
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="relative w-64 max-w-xs h-full z-10 flex-col"
            >
              <div className="absolute top-4 right-4 z-20">
                <button 
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1 rounded-md text-slate-400 hover:bg-slate-800 hover:text-white"
                >
                  <X size={20} />
                </button>
              </div>
              <SidebarContent />
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        
        {/* Sticky Header */}
        <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 sm:px-6 md:px-8 sticky top-0 z-40 shrink-0 shadow-sm transition-colors duration-200">
          
          {/* Left part: Hamburger (mobile) or Title (desktop) */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="lg:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-400"
            >
              <Menu size={20} />
            </button>
            <h2 className="hidden sm:block text-md font-bold tracking-tight text-slate-800 dark:text-slate-100">
              {getPageTitle()}
            </h2>
          </div>

          {/* Center search bar (designed like Linear / Vercel search) */}
          <div className="hidden md:flex items-center w-72 relative">
            <Search className="absolute left-3 text-slate-400" size={16} />
            <input 
              type="text" 
              placeholder="Search invoices, clients, or bills..."
              className="w-full text-xs pl-9 pr-3 py-1.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg outline-none focus:border-blue-500 dark:focus:border-blue-400 focus:ring-1 focus:ring-blue-500 transition-colors"
            />
          </div>

          {/* Right actions: Theme Toggle, Notifications, User Menu */}
          <div className="flex items-center gap-1.5 sm:gap-3">
            
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
            >
              {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
            </button>

            {/* Notifications Bell */}
            <div className="relative">
              <button
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors relative"
              >
                <Bell size={18} />
                <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-blue-500 rounded-full" />
              </button>
              
              <AnimatePresence>
                {notificationsOpen && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setNotificationsOpen(false)} />
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      className="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg z-50 p-4"
                    >
                      <div className="flex justify-between items-center pb-2 border-b border-slate-100 dark:border-slate-800">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Notifications</span>
                        <button className="text-[10px] text-blue-500 hover:underline">Mark all read</button>
                      </div>
                      <div className="py-2 space-y-2 max-h-60 overflow-y-auto">
                        <div className="p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                          <p className="text-xs font-semibold">New invoice uploaded</p>
                          <p className="text-[10px] text-slate-400 mt-0.5">Google LLC - $1,420.00 • 10m ago</p>
                        </div>
                        <div className="p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                          <p className="text-xs font-semibold">Approval rule triggered</p>
                          <p className="text-[10px] text-slate-400 mt-0.5">Required approval for invoice #1203 • 1h ago</p>
                        </div>
                      </div>
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>

            {/* Divider */}
            <div className="h-5 w-[1px] bg-slate-200 dark:bg-slate-800" />

            {/* Profile Dropdown */}
            <div className="relative">
              <button
                onClick={() => setProfileMenuOpen(!profileMenuOpen)}
                className="flex items-center gap-1.5 p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-xs">
                  {user.name ? user.name[0].toUpperCase() : 'U'}
                </div>
                <ChevronDown size={14} className="text-slate-400" />
              </button>
              
              <AnimatePresence>
                {profileMenuOpen && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setProfileMenuOpen(false)} />
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      className="absolute right-0 mt-2 w-52 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg z-50 py-1.5 overflow-hidden"
                    >
                      <div className="px-4 py-2 border-b border-slate-100 dark:border-slate-800">
                        <p className="text-xs font-bold truncate">{user.name || 'Admin User'}</p>
                        <p className="text-[10px] text-slate-400 truncate mt-0.5">{user.email || 'admin@example.com'}</p>
                      </div>
                      <button 
                        onClick={() => navigate('/settings/company')}
                        className="flex items-center gap-2 px-4 py-2 text-xs text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 w-full text-left"
                      >
                        <Settings size={14} />
                        <span>Company settings</span>
                      </button>
                      <button 
                        onClick={handleLogout}
                        className="flex items-center gap-2 px-4 py-2 text-xs text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20 w-full text-left border-t border-slate-100 dark:border-slate-800"
                      >
                        <LogOut size={14} />
                        <span>Sign Out</span>
                      </button>
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>

          </div>

        </header>

        {/* Scrollable Viewport Main */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-8">
          <div className="max-w-7xl mx-auto animate-fade-in-up">
            <Outlet />
          </div>
        </main>

      </div>
    </div>
  );
};

export default Layout;
