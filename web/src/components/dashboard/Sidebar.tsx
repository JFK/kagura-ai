'use client';

/**
 * Dashboard Sidebar Navigation
 *
 * Provides role-based navigation links for all dashboard sections.
 * Issue #664: Web UI Redesign Phase 1
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import { hasRole, Role } from '@/lib/rbac';
import {
  LayoutDashboard,
  Brain,
  List,
  Key,
  Settings,
  User,
  Users,
} from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  requiredRole?: Role;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const navigationGroups: NavGroup[] = [
  {
    title: 'Main',
    items: [
      {
        name: 'Dashboard',
        href: '/dashboard',
        icon: LayoutDashboard,
      },
    ],
  },
  {
    title: 'Memory',
    items: [
      {
        name: 'Memory Overview',
        href: '/memories',
        icon: Brain,
      },
      {
        name: 'Memory List',
        href: '/memories/list',
        icon: List,
      },
    ],
  },
  {
    title: 'Integration',
    items: [
      {
        name: 'API Keys',
        href: '/api-keys',
        icon: Key,
      },
    ],
  },
  {
    title: 'Settings',
    items: [
      {
        name: 'Config',
        href: '/settings/config',
        icon: Settings,
      },
      {
        name: 'Profile',
        href: '/settings/profile',
        icon: User,
      },
    ],
  },
  {
    title: 'Admin',
    items: [
      {
        name: 'User Management',
        href: '/admin/users',
        icon: Users,
        requiredRole: Role.ADMIN,
      },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  return (
    <aside className="flex flex-col w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
      {/* Logo */}
      <div className="flex items-center h-16 px-6 border-b border-slate-200 dark:border-slate-800">
        <Link href="/dashboard" className="flex items-center space-x-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <span className="text-white font-bold text-lg">K</span>
          </div>
          <span className="font-semibold text-lg">Kagura</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-6 overflow-y-auto">
        {navigationGroups.map((group) => {
          // Filter items based on user role
          const visibleItems = group.items.filter((item) => {
            if (!item.requiredRole) return true;
            return hasRole(user, item.requiredRole);
          });

          // Hide group if no items are visible
          if (visibleItems.length === 0) return null;

          return (
            <div key={group.title}>
              <h3 className="px-3 mb-2 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                {group.title}
              </h3>
              <div className="space-y-1">
                {visibleItems.map((item) => {
                  const isActive =
                    pathname === item.href ||
                    (item.href !== '/dashboard' && pathname.startsWith(item.href));
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
              </div>
            </div>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-200 dark:border-slate-800">
        {user && (
          <div className="mb-2 px-3">
            <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 truncate">
              {user.name}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {user.role || 'User'}
            </p>
          </div>
        )}
        <p className="text-xs text-slate-500 dark:text-slate-400 px-3">
          Kagura AI v4.4.0
        </p>
      </div>
    </aside>
  );
}
