'use client';

/**
 * System Backends Configuration Page
 *
 * Issue #684 - Backend Configuration and Monitoring
 * Full backend switching functionality with .env.cloud integration
 */

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  RefreshCw,
  AlertCircle,
  Database,
  HardDrive,
  Zap,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Save,
  Settings,
} from 'lucide-react';
import {
  getBackendStatus,
  getVectorCollections,
  restartApplication,
  pollHealth,
  type BackendStatusResponse,
  type VectorCollectionsResponse,
} from '@/lib/system';
import { getConfig, batchUpdateConfig, validateConfig } from '@/lib/config';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';

export default function SystemBackendsPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [backends, setBackends] = useState<BackendStatusResponse | null>(null);
  const [collections, setCollections] = useState<VectorCollectionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Backend selection state
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');
  const [selectedVectorDb, setSelectedVectorDb] = useState<string>('');
  const [selectedCache, setSelectedCache] = useState<string>('');
  const [hasChanges, setHasChanges] = useState(false);
  const [saving, setSaving] = useState(false);

  // Restart modal state
  const [showRestartModal, setShowRestartModal] = useState(false);
  const [restarting, setRestarting] = useState(false);

  const isAdmin = user?.role === 'admin';

  // Fetch backend status
  const fetchBackends = async () => {
    try {
      setLoading(true);
      setError(null);

      const [backendData, collectionsData, config] = await Promise.all([
        getBackendStatus(),
        getVectorCollections().catch(() => null), // Optional
        getConfig(true).catch(() => null), // Get current config
      ]);

      setBackends(backendData);
      setCollections(collectionsData);

      // Set current backend selections
      if (config) {
        const persistentBackend = config.config['PERSISTENT_BACKEND'] || backendData.database.type;
        const vectorBackend = config.config['VECTOR_BACKEND'] || backendData.vector_db.type;
        const cacheBackend = config.config['CACHE_BACKEND'] || backendData.cache.type;

        setSelectedDatabase(persistentBackend === 'postgres' ? 'postgres' : 'sqlite');
        setSelectedVectorDb(vectorBackend === 'qdrant' ? 'qdrant' : 'chromadb');
        setSelectedCache(cacheBackend === 'redis' ? 'redis' : 'memory');
      } else {
        // Fallback to current backend types
        setSelectedDatabase(backendData.database.type === 'postgres' ? 'postgres' : 'sqlite');
        setSelectedVectorDb(backendData.vector_db.type === 'qdrant' ? 'qdrant' : 'chromadb');
        setSelectedCache(backendData.cache.type === 'redis' ? 'redis' : 'memory');
      }

      setHasChanges(false);
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

  // Detect changes
  useEffect(() => {
    if (!backends) return;

    const currentDb = backends.database.type === 'postgres' ? 'postgres' : 'sqlite';
    const currentVector = backends.vector_db.type === 'qdrant' ? 'qdrant' : 'chromadb';
    const currentCache = backends.cache.type === 'redis' ? 'redis' : 'memory';

    const changed =
      selectedDatabase !== currentDb ||
      selectedVectorDb !== currentVector ||
      selectedCache !== currentCache;

    setHasChanges(changed);
  }, [selectedDatabase, selectedVectorDb, selectedCache, backends]);

  // Handle save backend configuration
  const handleSaveBackends = () => {
    // Validate requirements
    const errors: string[] = [];

    if (selectedDatabase === 'postgres' && !backends?.database.url?.includes('postgresql')) {
      errors.push('PostgreSQL selected but DATABASE_URL is not configured');
    }

    if (selectedVectorDb === 'qdrant' && !backends?.vector_db.url?.includes('6333')) {
      errors.push('Qdrant selected but QDRANT_URL is not configured');
    }

    if (selectedCache === 'redis' && !backends?.cache.url?.includes('redis')) {
      errors.push('Redis selected but REDIS_URL is not configured');
    }

    if (errors.length > 0) {
      toast({
        title: 'Configuration Error',
        description: errors.join('. '),
        variant: 'destructive',
      });
      return;
    }

    // Show restart confirmation dialog
    setShowRestartModal(true);
  };

  // Confirm and apply backend changes
  const handleConfirmRestart = async () => {
    try {
      setSaving(true);
      setRestarting(true);

      const updates = {
        PERSISTENT_BACKEND: selectedDatabase,
        VECTOR_BACKEND: selectedVectorDb,
        CACHE_BACKEND: selectedCache,
      };

      // Validate before saving
      const validation = await validateConfig(updates);
      if (!validation.valid) {
        const errorMessages = Object.values(validation.errors).join(', ');
        toast({
          title: 'Validation Failed',
          description: errorMessages,
          variant: 'destructive',
        });
        setSaving(false);
        setRestarting(false);
        return;
      }

      // Save to .env.cloud
      await batchUpdateConfig(updates);

      toast({
        title: 'Configuration Saved',
        description: 'Backend configuration updated in .env.cloud',
      });

      // Trigger application restart
      toast({
        title: 'Restarting Application',
        description: 'Please wait while the API container restarts (~30 seconds)...',
      });

      await restartApplication();

      // Poll health endpoint
      const healthy = await pollHealth(60, 1000);

      if (healthy) {
        toast({
          title: 'Application Restarted',
          description: 'Backend changes have been applied successfully.',
        });

        // Refresh backend status
        await fetchBackends();
      } else {
        toast({
          title: 'Restart Timeout',
          description: 'Application did not respond after restart. Please check manually.',
          variant: 'destructive',
        });
      }

      setShowRestartModal(false);
    } catch (err) {
      console.error('Failed to save backend configuration:', err);
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to save configuration',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
      setRestarting(false);
    }
  };

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
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">System Backends</h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Configure and monitor database, vector store, and cache backends
          </p>
        </div>

        <div className="flex gap-2">
          <Button onClick={fetchBackends} variant="outline" disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {hasChanges && (
            <Button onClick={handleSaveBackends} disabled={saving}>
              <Save className="h-4 w-4 mr-2" />
              Save & Restart
            </Button>
          )}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Backend Configuration Cards */}
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
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2">
                {getStatusIcon(backends.database.status)}
                <Badge variant={backends.database.connected ? 'default' : 'secondary'}>
                  {backends.database.type.toUpperCase()}
                </Badge>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                {backends.database.message}
              </p>

              {/* Backend Switcher */}
              <div className="space-y-2">
                <Label className="text-xs">Switch Backend:</Label>
                <Select value={selectedDatabase} onValueChange={setSelectedDatabase}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sqlite">SQLite</SelectItem>
                    <SelectItem value="postgres">PostgreSQL</SelectItem>
                  </SelectContent>
                </Select>
              </div>

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
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2">
                {getStatusIcon(backends.vector_db.status)}
                <Badge variant={backends.vector_db.connected ? 'default' : 'secondary'}>
                  {backends.vector_db.type.toUpperCase()}
                </Badge>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                {backends.vector_db.message}
              </p>

              {/* Backend Switcher */}
              <div className="space-y-2">
                <Label className="text-xs">Switch Backend:</Label>
                <Select value={selectedVectorDb} onValueChange={setSelectedVectorDb}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="chromadb">ChromaDB</SelectItem>
                    <SelectItem value="qdrant">Qdrant</SelectItem>
                  </SelectContent>
                </Select>
              </div>

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
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2">
                {getStatusIcon(backends.cache.status)}
                <Badge variant={backends.cache.connected ? 'default' : 'secondary'}>
                  {backends.cache.type.toUpperCase()}
                </Badge>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                {backends.cache.message}
              </p>

              {/* Backend Switcher */}
              <div className="space-y-2">
                <Label className="text-xs">Switch Backend:</Label>
                <Select value={selectedCache} onValueChange={setSelectedCache}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="memory">In-Memory</SelectItem>
                    <SelectItem value="redis">Redis</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {backends.cache.url && (
                <p className="text-xs text-slate-500 mt-2 font-mono truncate">
                  {backends.cache.url}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      ) : null}

      {/* Configuration Guide */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Backend Switching Requirements</AlertTitle>
        <AlertDescription>
          <div className="mt-2 space-y-2 text-sm">
            <p>Before switching to a backend, ensure the required environment variables are configured:</p>
            <ul className="list-disc list-inside space-y-1 ml-2 text-xs">
              <li>
                <strong>PostgreSQL</strong>: <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">DATABASE_URL</code> must be set
              </li>
              <li>
                <strong>Qdrant</strong>: <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">QDRANT_URL</code> must be set
              </li>
              <li>
                <strong>Redis</strong>: <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">REDIS_URL</code> must be set
              </li>
            </ul>
            <p className="mt-2">
              <strong>Note:</strong> Changing backends requires application restart (~30 seconds).
            </p>
          </div>
        </AlertDescription>
      </Alert>

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
                      <TableCell className="font-mono text-xs">{collection.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {collection.vector_count.toLocaleString()} vectors
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {collection.embedding_dimension ? (
                          <Badge variant="secondary">{collection.embedding_dimension}D</Badge>
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

      {/* Restart Confirmation Modal */}
      <Dialog open={showRestartModal} onOpenChange={setShowRestartModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Backend Configuration Change</DialogTitle>
            <DialogDescription>
              Changing backend configuration will restart the application. This process takes approximately 30 seconds.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-4">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-sm">
                <p className="font-medium mb-2">Changes to be applied:</p>
                <ul className="list-disc list-inside space-y-1 text-xs ml-2">
                  <li>Database: {backends?.database.type.toUpperCase()} → {selectedDatabase.toUpperCase()}</li>
                  <li>Vector DB: {backends?.vector_db.type.toUpperCase()} → {selectedVectorDb.toUpperCase()}</li>
                  <li>Cache: {backends?.cache.type.toUpperCase()} → {selectedCache.toUpperCase()}</li>
                </ul>
              </AlertDescription>
            </Alert>

            {restarting && (
              <Alert>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <AlertDescription className="text-sm">
                  Application is restarting... Please wait.
                </AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRestartModal(false)} disabled={restarting}>
              Cancel
            </Button>
            <Button onClick={handleConfirmRestart} disabled={restarting}>
              {restarting ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Restarting...
                </>
              ) : (
                <>
                  <Settings className="h-4 w-4 mr-2" />
                  Apply & Restart
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
