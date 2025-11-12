'use client';

/**
 * Dashboard Home Page
 *
 * Issue #651 - Unified page handling both landing and dashboard views
 * - Unauthenticated: Shows landing page with "Login with Google"
 * - Authenticated: Shows dashboard statistics and quick actions
 */

import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Database, TrendingUp, Users, Activity } from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();

  // Show landing page for unauthenticated users
  if (!user) {
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

  // Mock statistics (will be replaced with real API calls)
  const stats = [
    {
      title: 'Total Memories',
      value: '1,234',
      change: '+12.5%',
      icon: Database,
      description: 'from last month',
    },
    {
      title: 'Active Sessions',
      value: '42',
      change: '+5.2%',
      icon: Activity,
      description: 'from last week',
    },
    {
      title: 'API Requests',
      value: '8,492',
      change: '+18.3%',
      icon: TrendingUp,
      description: 'from yesterday',
    },
    {
      title: 'Total Users',
      value: '127',
      change: '+3.1%',
      icon: Users,
      description: 'from last month',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Message */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Welcome back, {user?.name?.split(' ')[0] || 'User'}!
        </h1>
        <p className="text-slate-500 dark:text-slate-400 mt-2">
          Here's what's happening with your memory cloud today.
        </p>
      </div>

      {/* Statistics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                <Icon className="h-4 w-4 text-slate-500 dark:text-slate-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  <span className="text-green-600 dark:text-green-400 font-medium">
                    {stat.change}
                  </span>{' '}
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Recent Activity */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Memories</CardTitle>
            <CardDescription>
              Your most recently created or updated memories
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="flex items-center gap-4 p-3 rounded-lg bg-slate-50 dark:bg-slate-800"
                >
                  <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      Memory Entry #{i}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      Updated {i} hour{i > 1 ? 's' : ''} ago
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common tasks and shortcuts
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                'Create New Memory',
                'Generate API Key',
                'View Analytics Report',
                'Export Data',
              ].map((action) => (
                <button
                  key={action}
                  className="w-full p-3 text-left rounded-lg bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                  <p className="text-sm font-medium">{action}</p>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
