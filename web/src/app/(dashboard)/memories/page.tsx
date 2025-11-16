'use client';

/**
 * Memory Overview Page
 *
 * Displays memory and coding memory statistics from doctor API.
 * Issue #664: Web UI Redesign Phase 1
 */

import { MemoryOverview } from '@/components/dashboard/MemoryOverview';
import { Button } from '@/components/ui/button';
import { Link } from 'lucide-react';

export default function MemoriesPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Memory Overview</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-2">
            Monitor your memory system health and coding session statistics.
          </p>
        </div>
        <Button asChild>
          <a href="/dashboard/memories/list">
            View All Memories
          </a>
        </Button>
      </div>

      {/* Memory Overview Metrics */}
      <MemoryOverview />
    </div>
  );
}
