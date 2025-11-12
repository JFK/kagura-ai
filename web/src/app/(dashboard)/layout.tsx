'use client';

/**
 * Dashboard Layout
 *
 * Provides the main layout for authenticated dashboard pages.
 * Includes sidebar navigation, header, and authentication guard.
 * Issue #651, #655 - Unified landing and dashboard handling
 */

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { Header } from '@/components/dashboard/Header';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // Redirect to login for protected routes (not homepage)
  useEffect(() => {
    if (!isLoading && !user && pathname !== '/') {
      router.push('/login');
    }
  }, [user, isLoading, pathname, router]);

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-10 w-10 rounded-full border-4 border-slate-200 border-t-slate-600 animate-spin" />
      </div>
    );
  }

  // For unauthenticated users on homepage (/), show landing page without dashboard chrome
  if (!user && pathname === '/') {
    return <>{children}</>;
  }

  // For protected routes, don't render if not authenticated (redirecting to login)
  if (!user) {
    return null;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Header */}
        <Header />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-900">
          <div className="container mx-auto p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
