'use client';

/**
 * Dashboard Metrics Component
 *
 * Displays system health metrics from doctor API.
 * Issue #664: Web UI Redesign Phase 1
 */

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
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
} from 'lucide-react';
import { getSystemDoctor, type SystemDoctorResponse } from '@/lib/doctor';

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
      return <Badge className="bg-green-500">Healthy</Badge>;
    case 'warning':
      return <Badge className="bg-yellow-500">Warning</Badge>;
    case 'error':
      return <Badge variant="destructive">Error</Badge>;
    default:
      return <Badge variant="secondary">Info</Badge>;
  }
}

export function DashboardMetrics() {
  const [data, setData] = useState<SystemDoctorResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
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
    }

    fetchData();
  }, []);

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Loading...</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-20 animate-pulse bg-gray-200 rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error || !data) {
    return (
      <Alert variant="destructive">
        <XCircle className="h-4 w-4" />
        <AlertDescription>{error || 'Failed to load metrics'}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {/* Overall Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            System Health Overview
          </CardTitle>
          <CardDescription>
            Overall status: {getStatusBadge(data.overall_status)}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Python Version */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Python Version</CardTitle>
            {getStatusIcon(data.python_version.status)}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.python_version.message}</div>
          </CardContent>
        </Card>

        {/* Disk Space */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Disk Space</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center gap-2">
              {getStatusIcon(data.disk_space.status)}
              <span className="text-lg">{data.disk_space.message}</span>
            </div>
          </CardContent>
        </Card>

        {/* Dependencies */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Dependencies</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.dependencies.length}</div>
            <p className="text-xs text-muted-foreground">
              {data.dependencies.filter((d) => d.status === 'ok').length} OK,{' '}
              {data.dependencies.filter((d) => d.status === 'warning').length} Warning
            </p>
          </CardContent>
        </Card>

        {/* API Configuration */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API Status</CardTitle>
            <Wifi className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.api_configuration.length}</div>
            <p className="text-xs text-muted-foreground">
              {data.api_configuration.filter((a) => a.status === 'ok').length} Connected
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Dependencies Detail */}
      {data.dependencies.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Dependency Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.dependencies.map((dep, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(dep.status)}
                    <span className="font-mono text-sm">{dep.name}</span>
                  </div>
                  <span className="text-sm text-muted-foreground">{dep.message}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* API Configuration Detail */}
      {data.api_configuration.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">API Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.api_configuration.map((api, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(api.status)}
                    <span className="font-semibold text-sm">{api.provider}</span>
                  </div>
                  <span className="text-sm text-muted-foreground">{api.message}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Backend Services - PostgreSQL (Issue #668) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Database className="h-4 w-4" />
            PostgreSQL
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            {getStatusIcon(data.postgres.status)}
            <span className="text-sm">{data.postgres.message}</span>
          </div>
        </CardContent>
      </Card>

      {/* Backend Services - Redis (Issue #668) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Redis Cache
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            {getStatusIcon(data.redis.status)}
            <span className="text-sm">{data.redis.message}</span>
          </div>
        </CardContent>
      </Card>

      {/* Backend Services - Qdrant (Issue #668) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Database className="h-4 w-4" />
            Qdrant Vector DB
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            {getStatusIcon(data.qdrant.status)}
            <span className="text-sm">{data.qdrant.message}</span>
          </div>
        </CardContent>
      </Card>

      {/* Remote MCP Server (Issue #668) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Puzzle className="h-4 w-4" />
            Remote MCP
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            {getStatusIcon(data.remote_mcp.status)}
            <span className="text-sm">{data.remote_mcp.message}</span>
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      {data.recommendations.length > 0 && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            <div className="font-semibold mb-2">Recommendations:</div>
            <ul className="list-disc list-inside space-y-1">
              {data.recommendations.map((rec, index) => (
                <li key={index} className="text-sm">
                  {rec}
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
