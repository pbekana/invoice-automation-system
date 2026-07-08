import { useState } from 'react';
import { Search, Bell, User, Moon, Sun, Menu } from 'lucide-react';
import { Button } from '../ui/Button';
import { Avatar } from '../ui/Avatar';
import useAuthStore from '../../store/useAuthStore';
import useThemeStore from '../../store/useThemeStore';

export function Header({ onMenuClick }) {
  const [searchQuery, setSearchQuery] = useState('');
  const user = useAuthStore(state => state.user);
  const { theme, toggleTheme } = useThemeStore();

  return (
    <header className="h-16 bg-white dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between px-6 sticky top-0 z-20">
      {/* Left: Mobile menu + Search */}
      <div className="flex items-center gap-4 flex-1 min-w-0">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-colors flex-shrink-0"
        >
          <Menu className="w-5 h-5 text-neutral-700 dark:text-neutral-300" />
        </button>

        <div className="relative w-full max-w-md hidden sm:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400 dark:text-neutral-500 pointer-events-none z-10" />
          <input
            type="search"
            placeholder="Search invoices, vendors..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-10 py-2 rounded-lg border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 dark:placeholder:text-neutral-500 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 dark:text-neutral-500 hover:text-neutral-600 dark:hover:text-neutral-300 z-10"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2 flex-shrink-0 ml-4">
        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleTheme}
          icon={theme === 'dark' ? Sun : Moon}
          className="hidden sm:flex"
        />

        {/* Notifications */}
        <Button variant="ghost" size="sm" className="relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-error-500 rounded-full" />
        </Button>

        {/* User Menu */}
        <div className="flex items-center gap-3 pl-2 ml-2 border-l border-neutral-200 dark:border-neutral-700">
          <div className="text-right hidden md:block">
            <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
              {user?.name || 'User'}
            </p>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              {user?.email || 'user@example.com'}
            </p>
          </div>
          <Avatar 
            name={user?.name || 'User'} 
            size="md"
          />
        </div>
      </div>
    </header>
  );
}
