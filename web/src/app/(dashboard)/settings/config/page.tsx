'use client';

/**
 * Configuration Settings Page
 *
 * Coming Soon: External service configuration (API keys, models, etc.)
 * Issue #664: Web UI Redesign Phase 1
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Info, Settings } from 'lucide-react';

export default function ConfigPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Configuration</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-2">
          Manage external service configurations and settings.
        </p>
      </div>

      {/* Coming Soon Alert */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          <div className="font-semibold mb-1">Coming Soon</div>
          <p className="text-sm">
            This page will allow you to configure external API keys, model settings, and other
            integration parameters. Check back in the next release!
          </p>
        </AlertDescription>
      </Alert>

      {/* Preview Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Planned Features
          </CardTitle>
          <CardDescription>Features that will be available in this section</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-blue-500" />
              External API Key Management (OpenAI, Anthropic, etc.)
            </li>
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-blue-500" />
              Model Selection and Configuration
            </li>
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-blue-500" />
              Integration Settings (GitHub, GitLab, etc.)
            </li>
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-blue-500" />
              Environment Variable Management
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
