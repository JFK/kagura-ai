'use client';

/**
 * Dashboard Top Page
 *
 * Displays system health metrics from kagura doctor.
 * Issue #664: Web UI Redesign Phase 1
 */

import { DashboardMetrics } from '@/components/dashboard/DashboardMetrics';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Dashboard</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-2">
          Monitor your Kagura Memory Cloud system health and status.
        </p>
      </div>

      {/* Dashboard Metrics */}
      <DashboardMetrics />
    </div>
  );
}
