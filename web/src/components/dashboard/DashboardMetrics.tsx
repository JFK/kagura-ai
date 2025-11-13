'use client';

/**
 * Dashboard Metrics Component - Premium Redesign
 *
 * Professional design matching landing page quality
 * Uses gradient cards, animations, and modern layout
 */

import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { GradientCard } from '@/components/ui/gradient-card';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Server,
  HardDrive,
  Package,
  Wifi,
  Puzzle,
  Database,
  Zap,
  Activity,
  RefreshCw,
} from 'lucide-react';
import { getSystemDoctor, type SystemDoctorResponse } from '@/lib/doctor';
import { Button } from '@/components/ui/button';

function getStatusIcon(status: string) {
  switch (status) {
    case 'ok':
      return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    case 'warning':
      return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    case 'error':
      return <XCircle className="h-4 w-4 text-red-500" />;
    default:
      return <Info className="h-4 w-4 text-blue-500" />;
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case 'ok':
      return (
        <Badge className="border-0 bg-gradient-to-r from-green-500 to-emerald-500 text-white">
          Healthy
        </Badge>
      );
    case 'warning':
      return (
        <Badge className="border-0 bg-gradient-to-r from-yellow-500 to-orange-500 text-white">
          Warning
        </Badge>
      );
    case 'error':
      return (
        <Badge className="border-0 bg-gradient-to-r from-red-500 to-rose-500 text-white">
          Error
        </Badge>
      );
    default:
      return <Badge variant="secondary">Info</Badge>;
  }
}

export function DashboardMetrics() {
  const [data, setData] = useState<SystemDoctorResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const response = await getSystemDoctor();
      setData(response);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch system doctor:', err);
      setError(err instanceof Error ? err.message : 'Failed to load system health');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        {/* Loading Message */}
        <div className="flex items-center justify-center rounded-2xl border-2 border-brand-green-200 bg-gradient-to-r from-brand-green-50 to-emerald-50 p-8">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="h-12 w-12 animate-spin rounded-full border-4 border-brand-green-200 border-t-brand-green-600" />
              <div className="absolute inset-0 h-12 w-12 animate-ping rounded-full border-4 border-brand-green-600 opacity-20" />
            </div>
            <div>
              <p className="text-lg font-semibold text-gray-900">Loading system metrics...</p>
              <p className="text-sm text-gray-600">Gathering health information</p>
            </div>
          </div>
        </div>

        {/* Skeleton Cards */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="overflow-hidden">
              <CardContent className="p-6">
                <div className="h-32 animate-pulse rounded-lg bg-gradient-to-br from-brand-green-100 to-emerald-100" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <Alert variant="destructive" className="border-red-200 bg-red-50">
        <XCircle className="h-5 w-5" />
        <AlertDescription className="text-base">
          {error || 'Failed to load metrics'}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overall System Status - Hero Card */}
      <Card className="overflow-hidden border-gray-200 bg-gradient-to-br from-white to-gray-50">
        <CardContent className="p-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-gradient-to-br from-brand-green-500 to-emerald-500 p-4 text-white shadow-lg">
                <Server className="h-8 w-8" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900">System Health</h3>
                <p className="text-gray-600">Overall Status</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {getStatusBadge(data.overall_status)}
              <Button
                variant="outline"
                size="sm"
                onClick={fetchData}
                disabled={isLoading}
                className="border-gray-300"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* Python Version */}
        <GradientCard
          icon={Activity}
          title="Python Version"
          value={data.python_version.message}
          gradient="from-blue-500 to-cyan-500"
        />

        {/* Disk Space */}
        <GradientCard
          icon={HardDrive}
          title="Disk Space"
          value={data.disk_space.message}
          gradient="from-purple-500 to-pink-500"
        />

        {/* Dependencies */}
        <GradientCard
          icon={Package}
          title="Dependencies"
          value={`${data.dependencies.length}`}
          description={`${data.dependencies.filter((d) => d.status === 'ok').length} OK, ${data.dependencies.filter((d) => d.status === 'warning').length} Warning`}
          gradient="from-green-500 to-emerald-500"
        />

        {/* API Status */}
        <GradientCard
          icon={Wifi}
          title="API Status"
          value={`${data.api_configuration.filter((a) => a.status === 'ok').length}/${data.api_configuration.length}`}
          description="Connected"
          gradient="from-orange-500 to-red-500"
        />
      </div>

      {/* Backend Services Grid */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Backend Services</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {/* PostgreSQL */}
          <Card className="group overflow-hidden border-gray-200 bg-white transition-all hover:border-brand-green-300 hover:shadow-lg">
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-blue-50 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
            <CardContent className="relative p-6">
              <div className="mb-3 flex items-center justify-between">
                <div className="inline-flex rounded-lg bg-blue-100 p-2 text-blue-600">
                  <Database className="h-5 w-5" />
                </div>
                {getStatusIcon(data.postgres.status)}
              </div>
              <h4 className="mb-1 font-semibold text-gray-900">PostgreSQL</h4>
              <p className="text-sm text-gray-600">{data.postgres.message}</p>
            </CardContent>
          </Card>

          {/* Redis */}
          <Card className="group overflow-hidden border-gray-200 bg-white transition-all hover:border-brand-green-300 hover:shadow-lg">
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-red-50 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
            <CardContent className="relative p-6">
              <div className="mb-3 flex items-center justify-between">
                <div className="inline-flex rounded-lg bg-red-100 p-2 text-red-600">
                  <Zap className="h-5 w-5" />
                </div>
                {getStatusIcon(data.redis.status)}
              </div>
              <h4 className="mb-1 font-semibold text-gray-900">Redis Cache</h4>
              <p className="text-sm text-gray-600">{data.redis.message}</p>
            </CardContent>
          </Card>

          {/* Qdrant */}
          <Card className="group overflow-hidden border-gray-200 bg-white transition-all hover:border-brand-green-300 hover:shadow-lg">
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-purple-50 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
            <CardContent className="relative p-6">
              <div className="mb-3 flex items-center justify-between">
                <div className="inline-flex rounded-lg bg-purple-100 p-2 text-purple-600">
                  <Database className="h-5 w-5" />
                </div>
                {getStatusIcon(data.qdrant.status)}
              </div>
              <h4 className="mb-1 font-semibold text-gray-900">Qdrant Vector DB</h4>
              <p className="text-sm text-gray-600">{data.qdrant.message}</p>
            </CardContent>
          </Card>

          {/* Remote MCP */}
          <Card className="group overflow-hidden border-gray-200 bg-white transition-all hover:border-brand-green-300 hover:shadow-lg">
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-green-50 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
            <CardContent className="relative p-6">
              <div className="mb-3 flex items-center justify-between">
                <div className="inline-flex rounded-lg bg-brand-green-100 p-2 text-brand-green-600">
                  <Puzzle className="h-5 w-5" />
                </div>
                {getStatusIcon(data.remote_mcp.status)}
              </div>
              <h4 className="mb-1 font-semibold text-gray-900">Remote MCP</h4>
              <p className="text-sm text-gray-600">{data.remote_mcp.message}</p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* API Configuration & Dependencies (Two Columns) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* API Configuration */}
        {data.api_configuration.length > 0 && (
          <Card className="border-gray-200">
            <CardContent className="p-6">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-full bg-gradient-to-br from-brand-green-500 to-emerald-500 p-3 text-white">
                  <Wifi className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">API Configuration</h3>
              </div>
              <div className="space-y-3">
                {data.api_configuration.map((api, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-3 transition-colors hover:bg-gray-100"
                  >
                    <div className="flex items-center gap-3">
                      {getStatusIcon(api.status)}
                      <span className="font-medium text-gray-900">{api.provider}</span>
                    </div>
                    <span className="text-sm text-gray-600">{api.message}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Dependencies */}
        {data.dependencies.length > 0 && (
          <Card className="border-gray-200">
            <CardContent className="p-6">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-full bg-gradient-to-br from-purple-500 to-pink-500 p-3 text-white">
                  <Package className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Dependencies</h3>
              </div>
              <div className="space-y-3">
                {data.dependencies.map((dep, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-3 transition-colors hover:bg-gray-100"
                  >
                    <div className="flex items-center gap-3">
                      {getStatusIcon(dep.status)}
                      <span className="font-mono text-sm font-medium text-gray-900">
                        {dep.name}
                      </span>
                    </div>
                    <span className="text-sm text-gray-600">{dep.message}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Recommendations */}
      {data.recommendations.length > 0 && (
        <Alert className="border-2 border-blue-200 bg-gradient-to-r from-blue-50 to-transparent">
          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <div className="rounded-full bg-blue-100 p-2">
                <Info className="h-5 w-5 text-blue-600" />
              </div>
            </div>
            <AlertDescription>
              <div className="mb-3 text-base font-semibold text-gray-900">
                Recommendations
              </div>
              <div className="space-y-2">
                {data.recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-600" />
                    <span>{rec}</span>
                  </div>
                ))}
              </div>
            </AlertDescription>
          </div>
        </Alert>
      )}
    </div>
  );
}
