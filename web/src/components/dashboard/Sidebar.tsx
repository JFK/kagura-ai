'use client';

/**
 * Dashboard Sidebar Navigation
 *
 * Provides navigation links for all dashboard sections.
 * Responsive design with collapsible menu for mobile.
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Database,
  BarChart3,
  Key,
  Settings,
} from 'lucide-react';

const navigation = [
  {
    name: 'Dashboard',
    href: '/',
    icon: LayoutDashboard,
  },
  {
    name: 'Memories',
    href: '/memories',
    icon: Database,
  },
  {
    name: 'API Keys',
    href: '/api-keys',
    icon: Key,
  },
  // TODO: Implement remaining pages (Issue #651)
  // {
  //   name: 'Analytics',
  //   href: '/analytics',
  //   icon: BarChart3,
  // },
  // {
  //   name: 'Settings',
  //   href: '/settings',
  //   icon: Settings,
  // },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex flex-col w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
      {/* Logo */}
      <div className="flex items-center h-16 px-6 border-b border-slate-200 dark:border-slate-800">
        <Link href="/" className="flex items-center space-x-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <span className="text-white font-bold text-lg">K</span>
          </div>
          <span className="font-semibold text-lg">Kagura</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-white'
              )}
            >
              <Icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-200 dark:border-slate-800">
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Kagura AI v4.4.0
        </p>
      </div>
    </aside>
  );
}
