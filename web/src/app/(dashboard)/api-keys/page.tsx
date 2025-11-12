'use client';

/**
 * API Keys Management Page
 *
 * Issue #655 - API Key Management Page with CRUD Operations
 * Displays list of API keys with create, revoke, stats, and delete operations
 */

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Plus, Search, RefreshCw, AlertCircle } from 'lucide-react';
import { getAPIKeys } from '@/lib/api-keys';
import type { APIKey, APIKeyStatus } from '@/lib/types/api-key';
import { APIKeysTable } from '@/components/api-keys/APIKeysTable';
import { CreateAPIKeyDialog } from '@/components/api-keys/CreateAPIKeyDialog';
import { APIKeyStatsDialog } from '@/components/api-keys/APIKeyStatsDialog';
import { RevokeAPIKeyDialog } from '@/components/api-keys/RevokeAPIKeyDialog';
import { DeleteAPIKeyDialog } from '@/components/api-keys/DeleteAPIKeyDialog';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export default function APIKeysPage() {
  const { user } = useAuth();
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<APIKeyStatus | 'all'>('all');

  // Dialogs
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [statsKeyId, setStatsKeyId] = useState<number | null>(null);
  const [statsKeyName, setStatsKeyName] = useState<string | null>(null);
  const [revokeKey, setRevokeKey] = useState<{ id: number; name: string } | null>(null);
  const [deleteKey, setDeleteKey] = useState<{ id: number; name: string } | null>(null);

  // Check if user is admin
  const isAdmin = user?.role === 'admin';

  // Fetch API keys
  const fetchAPIKeys = async () => {
    if (!user || !isAdmin) return;

    try {
      setLoading(true);
      setError(null);

      const keys = await getAPIKeys();
      setApiKeys(keys || []);
    } catch (err) {
      console.error('Failed to fetch API keys:', err);
      setError(err instanceof Error ? err.message : 'Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  // Load API keys on mount
  useEffect(() => {
    if (isAdmin) {
      fetchAPIKeys();
    } else {
      setLoading(false);
    }
  }, [user, isAdmin]);

  const handleRefresh = () => {
    fetchAPIKeys();
  };

  const handleKeyCreated = () => {
    setCreateDialogOpen(false);
    fetchAPIKeys();
  };

  const handleKeyRevoked = () => {
    setRevokeKey(null);
    fetchAPIKeys();
  };

  const handleKeyDeleted = () => {
    setDeleteKey(null);
    fetchAPIKeys();
  };

  const handleShowStats = (keyId: number, keyName: string) => {
    setStatsKeyId(keyId);
    setStatsKeyName(keyName);
  };

  const handleCloseStats = () => {
    setStatsKeyId(null);
    setStatsKeyName(null);
  };

  // Filter keys based on search and status
  const filteredKeys = apiKeys.filter((key) => {
    const matchesSearch =
      !searchQuery ||
      key.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      key.key_prefix.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'all' || key.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  // Non-admin users
  if (!isAdmin) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Access Denied</AlertTitle>
          <AlertDescription>
            Only administrators can manage API keys. Please contact your administrator.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">API Keys</h1>
          <p className="text-muted-foreground mt-1">
            Manage programmatic access to Kagura Memory API
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create API Key
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name or key prefix..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as APIKeyStatus | 'all')}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="revoked">Revoked</SelectItem>
            <SelectItem value="expired">Expired</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" onClick={handleRefresh}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Error message */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Table */}
      <APIKeysTable
        apiKeys={filteredKeys}
        loading={loading}
        onShowStats={handleShowStats}
        onRevoke={(key) => setRevokeKey({ id: key.id, name: key.name })}
        onDelete={(key) => setDeleteKey({ id: key.id, name: key.name })}
      />

      {/* Dialogs */}
      <CreateAPIKeyDialog
        isOpen={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={handleKeyCreated}
      />

      {statsKeyId && statsKeyName && (
        <APIKeyStatsDialog
          isOpen={true}
          keyId={statsKeyId}
          keyName={statsKeyName}
          onClose={handleCloseStats}
        />
      )}

      {revokeKey && (
        <RevokeAPIKeyDialog
          isOpen={true}
          keyId={revokeKey.id}
          keyName={revokeKey.name}
          onClose={() => setRevokeKey(null)}
          onSuccess={handleKeyRevoked}
        />
      )}

      {deleteKey && (
        <DeleteAPIKeyDialog
          isOpen={true}
          keyId={deleteKey.id}
          keyName={deleteKey.name}
          onClose={() => setDeleteKey(null)}
          onSuccess={handleKeyDeleted}
        />
      )}
    </div>
  );
}
