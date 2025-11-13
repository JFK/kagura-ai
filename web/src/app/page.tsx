'use client';

/**
 * Root/Landing Page
 *
 * - Unauthenticated: Shows landing page with "Login with Google"
 * - Authenticated: Redirects to /dashboard
 *
 * Issue #664: Web UI Redesign Phase 1
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';

export default function LandingPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (!isLoading && user) {
      router.push('/dashboard');
    }
  }, [user, isLoading, router]);

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600 mx-auto" />
          <p className="mt-4 text-sm text-gray-600">Loading...</p>
        </div>
      </main>
    );
  }

  // Show landing page for unauthenticated users
  if (!user) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-slate-900 dark:to-slate-800">
        <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
          <div className="text-center mb-12">
            <Image
              src="/kagura-logo.svg"
              alt="Kagura AI Logo"
              width={80}
              height={80}
              className="mx-auto mb-4"
              priority
            />
            <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Kagura Memory Cloud
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
              Universal AI Memory & Context Platform
            </p>
          </div>

          <div className="mb-16 grid text-center lg:mb-0 lg:grid-cols-3 lg:text-left gap-6">
            <div className="group rounded-lg border border-gray-200 dark:border-gray-700 px-5 py-4 transition-colors hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-slate-800">
              <h2 className="mb-3 text-2xl font-semibold">
                System Health
              </h2>
              <p className="m-0 max-w-[30ch] text-sm opacity-70">
                Monitor your system status, dependencies, and API configuration
              </p>
            </div>

            <div className="group rounded-lg border border-gray-200 dark:border-gray-700 px-5 py-4 transition-colors hover:border-purple-500 hover:bg-purple-50 dark:hover:bg-slate-800">
              <h2 className="mb-3 text-2xl font-semibold">
                Memory Management
              </h2>
              <p className="m-0 max-w-[30ch] text-sm opacity-70">
                Manage your AI memory database and coding sessions
              </p>
            </div>

            <div className="group rounded-lg border border-gray-200 dark:border-gray-700 px-5 py-4 transition-colors hover:border-green-500 hover:bg-green-50 dark:hover:bg-slate-800">
              <h2 className="mb-3 text-2xl font-semibold">
                API Integration
              </h2>
              <p className="m-0 max-w-[30ch] text-sm opacity-70">
                Configure API keys for MCP and external services
              </p>
            </div>
          </div>

          <div className="flex justify-center mt-12">
            <Button
              size="lg"
              className="px-8 py-6 text-lg"
              onClick={() => router.push('/login')}
            >
              Login with Google
            </Button>
          </div>

          <p className="text-center mt-12 text-sm text-gray-500 dark:text-gray-400">
            Powered by Kagura AI v4.4.0 | Managed Service
          </p>
        </div>
      </main>
    );
  }

  // Should not reach here (redirect in useEffect)
  return null;
}
