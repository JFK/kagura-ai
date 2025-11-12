/**
 * Kagura Memory Cloud - Landing/Login Page
 * Issue #651 - Web Admin Dashboard
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function Home() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // If user is authenticated, redirect to dashboard
    if (!isLoading && user) {
      router.push('/memories');
    }
  }, [user, isLoading, router]);

  // Show landing page only if not authenticated
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-10 w-10 rounded-full border-4 border-slate-200 border-t-slate-600 animate-spin" />
      </div>
    );
  }

  if (user) {
    // Redirecting to dashboard
    return null;
  }
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-8 text-center">
          Kagura Memory Cloud
        </h1>

        <div className="mb-32 grid text-center lg:mb-0 lg:grid-cols-3 lg:text-left">
          <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors">
            <h2 className="mb-3 text-2xl font-semibold">
              Dashboard
            </h2>
            <p className="m-0 max-w-[30ch] text-sm opacity-50">
              View your memory statistics and recent activities
            </p>
          </div>

          <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors">
            <h2 className="mb-3 text-2xl font-semibold">
              Memories
            </h2>
            <p className="m-0 max-w-[30ch] text-sm opacity-50">
              Manage your AI memory database
            </p>
          </div>

          <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors">
            <h2 className="mb-3 text-2xl font-semibold">
              Settings
            </h2>
            <p className="m-0 max-w-[30ch] text-sm opacity-50">
              Configure API keys and preferences
            </p>
          </div>
        </div>

        <div className="flex justify-center mt-8">
          <a
            href="/login"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Login with Google
          </a>
        </div>

        <p className="text-center mt-8 text-sm opacity-50">
          Powered by Kagura AI v4.4.0
        </p>
      </div>
    </main>
  );
}
