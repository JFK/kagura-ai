'use client';

/**
 * Memory Overview Component
 *
 * Displays memory and coding memory statistics from doctor API.
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
  Database,
  Brain,
  Code2,
  FolderGit2,
  FileText,
} from 'lucide-react';
import {
  getMemoryDoctor,
  getCodingDoctor,
  type MemoryDoctorResponse,
  type CodingDoctorResponse,
} from '@/lib/doctor';
import { MemoryStatsChart } from './MemoryStatsChart';

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

export function MemoryOverview() {
  const [memoryData, setMemoryData] = useState<MemoryDoctorResponse | null>(null);
  const [codingData, setCodingData] = useState<CodingDoctorResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true);
        const [memory, coding] = await Promise.all([getMemoryDoctor(), getCodingDoctor()]);
        setMemoryData(memory);
        setCodingData(coding);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch memory doctor:', err);
        setError(err instanceof Error ? err.message : 'Failed to load memory health');
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, []);

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
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

  if (error || !memoryData || !codingData) {
    return (
      <Alert variant="destructive">
        <XCircle className="h-4 w-4" />
        <AlertDescription>{error || 'Failed to load memory statistics'}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {/* Memory System Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Memory System Health
          </CardTitle>
          <CardDescription>
            Overall status: {getStatusBadge(memoryData.status)}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Memory Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Database */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Database</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {memoryData.stats.database_exists ? (
                <>
                  {memoryData.stats.database_size_mb?.toFixed(1) || '0'}{' '}
                  <span className="text-sm">MB</span>
                </>
              ) : (
                'Not initialized'
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              {memoryData.stats.persistent_count.toLocaleString()} memories
            </p>
          </CardContent>
        </Card>

        {/* RAG Vectors */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">RAG Vectors</CardTitle>
            {getStatusIcon(memoryData.stats.rag_enabled ? 'ok' : 'warning')}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {memoryData.stats.rag_count.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {memoryData.stats.rag_enabled ? 'Enabled' : 'Disabled'}
            </p>
          </CardContent>
        </Card>

        {/* Reranking */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reranking</CardTitle>
            {getStatusIcon(
              memoryData.stats.reranking_enabled
                ? 'ok'
                : memoryData.stats.reranking_model_installed
                  ? 'warning'
                  : 'info'
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {memoryData.stats.reranking_enabled ? 'Enabled' : 'Disabled'}
            </div>
            <p className="text-xs text-muted-foreground">
              Model: {memoryData.stats.reranking_model_installed ? 'Installed' : 'Not installed'}
            </p>
          </CardContent>
        </Card>

        {/* Coding Sessions */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Coding Sessions</CardTitle>
            <Code2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {codingData.stats.sessions_count.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {codingData.stats.projects_count} projects
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Coding Memory Details */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <FolderGit2 className="h-4 w-4" />
            Coding Memory
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-2">
                <FolderGit2 className="h-5 w-5 text-muted-foreground" />
                <span className="font-semibold">Tracked Projects</span>
              </div>
              <span className="text-2xl font-bold">{codingData.stats.projects_count}</span>
            </div>
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-muted-foreground" />
                <span className="font-semibold">Coding Sessions</span>
              </div>
              <span className="text-2xl font-bold">{codingData.stats.sessions_count}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Memory & Coding Statistics Charts */}
      <MemoryStatsChart
        memoryData={memoryData.stats}
        codingData={codingData.stats}
      />

      {/* Recommendations */}
      {memoryData.recommendations.length > 0 && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            <div className="font-semibold mb-2">Recommendations:</div>
            <ul className="list-disc list-inside space-y-1">
              {memoryData.recommendations.map((rec, index) => (
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
