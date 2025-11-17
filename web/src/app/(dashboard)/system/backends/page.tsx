'use client';

/**
 * System Backends Status Page
 *
 * Issue #684 - Backend Configuration and Monitoring
 * Displays backend status (Database, Vector DB, Cache) and vector collections
 */

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { RefreshCw, AlertCircle, Database, HardDrive, Zap, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import {
  getBackendStatus,
  getVectorCollections,
  type BackendStatusResponse,
  type VectorCollectionsResponse,
} from '@/lib/system';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function SystemBackendsPage() {
  const { user } = useAuth();
  const [backends, setBackends] = useState<BackendStatusResponse | null>(null);
  const [collections, setCollections] = useState<VectorCollectionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAdmin = user?.role === 'admin';

  // Fetch backend status
  const fetchBackends = async () => {
    try {
      setLoading(true);
      setError(null);

      const [backendData, collectionsData] = await Promise.all([
        getBackendStatus(),
        getVectorCollections().catch(() => null), // Optional
      ]);

      setBackends(backendData);
      setCollections(collectionsData);
    } catch (err) {
      console.error('Failed to fetch backend status:', err);
      setError(err instanceof Error ? err.message : 'Failed to load backend status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      fetchBackends();
    } else {
      setLoading(false);
    }
  }, [isAdmin]);

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ok':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-blue-500" />;
    }
  };

  // Get backend icon
  const getBackendIcon = (type: string) => {
    if (type.includes('postgres') || type.includes('sqlite')) {
      return <Database className="h-6 w-6" />;
    }
    if (type.includes('qdrant') || type.includes('chroma')) {
      return <HardDrive className="h-6 w-6" />;
    }
    return <Zap className="h-6 w-6" />;
  };

  // Non-admin view
  if (!isAdmin) {
    return (
      <div className="p-8">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Admin Access Required</AlertTitle>
          <AlertDescription>
            Backend configuration is only available to administrators.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            System Backends
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Monitor database, vector store, and cache backend status
          </p>
        </div>

        <Button
          onClick={fetchBackends}
          variant="outline"
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Backend Status Cards */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
        </div>
      ) : backends ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Database Backend */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Database</CardTitle>
              {getBackendIcon(backends.database.type)}
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 mb-2">
                {getStatusIcon(backends.database.status)}
                <Badge variant={backends.database.connected ? 'default' : 'secondary'}>
                  {backends.database.type.toUpperCase()}
                </Badge>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                {backends.database.message}
              </p>
              {backends.database.url && (
                <p className="text-xs text-slate-500 mt-2 font-mono truncate">
                  {backends.database.url}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Vector DB Backend */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Vector Database</CardTitle>
              {getBackendIcon(backends.vector_db.type)}
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 mb-2">
                {getStatusIcon(backends.vector_db.status)}
                <Badge variant={backends.vector_db.connected ? 'default' : 'secondary'}>
                  {backends.vector_db.type.toUpperCase()}
                </Badge>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                {backends.vector_db.message}
              </p>
              {backends.vector_db.url && (
                <p className="text-xs text-slate-500 mt-2 font-mono truncate">
                  {backends.vector_db.url}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Cache Backend */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Cache</CardTitle>
              {getBackendIcon(backends.cache.type)}
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 mb-2">
                {getStatusIcon(backends.cache.status)}
                <Badge variant={backends.cache.connected ? 'default' : 'secondary'}>
                  {backends.cache.type.toUpperCase()}
                </Badge>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                {backends.cache.message}
              </p>
              {backends.cache.url && (
                <p className="text-xs text-slate-500 mt-2 font-mono truncate">
                  {backends.cache.url}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      ) : null}

      {/* Vector Collections */}
      {collections && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
            Vector Collections ({collections.backend.toUpperCase()})
          </h2>

          <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Collection Name</TableHead>
                  <TableHead>Vector Count</TableHead>
                  <TableHead>Embedding Dimension</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {collections.collections.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center py-8">
                      <p className="text-sm text-slate-500">No collections found</p>
                    </TableCell>
                  </TableRow>
                ) : (
                  collections.collections.map((collection) => (
                    <TableRow key={collection.name}>
                      <TableCell className="font-mono text-xs">
                        {collection.name}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {collection.vector_count.toLocaleString()} vectors
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {collection.embedding_dimension ? (
                          <Badge variant="secondary">
                            {collection.embedding_dimension}D
                          </Badge>
                        ) : (
                          <span className="text-xs text-slate-400">N/A</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </div>
  );
}
