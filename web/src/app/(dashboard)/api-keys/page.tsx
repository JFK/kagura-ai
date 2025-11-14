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
import { Plus, Search, RefreshCw, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
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

  // Setup Guide toggle (collapsed by default to save space)
  const [setupGuideOpen, setSetupGuideOpen] = useState(false);

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
    <div className="space-y-6">
      {/* Premium Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand-green-100 to-emerald-100 px-4 py-1.5 text-sm font-semibold text-brand-green-700">
            <Plus className="h-4 w-4" />
            <span>API Management</span>
          </div>
          <h1 className="text-4xl font-bold text-gray-900">API Keys</h1>
          <p className="mt-2 text-lg text-gray-600">
            Manage programmatic access to Kagura Memory API
          </p>
        </div>
        <Button
          size="lg"
          onClick={() => setCreateDialogOpen(true)}
          className="bg-gradient-to-r from-brand-green-600 to-emerald-600 text-white shadow-lg hover:from-brand-green-700 hover:to-emerald-700"
        >
          <Plus className="mr-2 h-5 w-5" />
          Create API Key
        </Button>
      </div>

      {/* Filters with Premium Styling */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <Input
            placeholder="Search by name or key prefix..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-11 border-gray-300 bg-white pl-10 shadow-sm transition-all focus:border-brand-green-500 focus:ring-2 focus:ring-brand-green-500/20"
          />
        </div>
        <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as APIKeyStatus | 'all')}>
          <SelectTrigger className="h-11 w-[180px] border-gray-300 bg-white shadow-sm">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="revoked">Revoked</SelectItem>
            <SelectItem value="expired">Expired</SelectItem>
          </SelectContent>
        </Select>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={loading}
          className="h-11 border-gray-300"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
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

      {/* Remote MCP Setup Guide - Collapsible, only show after API key is created */}
      {apiKeys.length > 0 && (
        <div className="rounded-2xl border-2 border-brand-green-200 bg-gradient-to-br from-brand-green-50 to-emerald-50">
          {/* Collapsible Header */}
          <button
            onClick={() => setSetupGuideOpen(!setupGuideOpen)}
            className="w-full p-6 flex items-start gap-4 hover:bg-brand-green-100/50 transition-colors rounded-t-2xl text-left"
          >
            <div className="flex-shrink-0 rounded-lg bg-brand-green-600 p-3 text-white">
              <AlertCircle className="h-6 w-6" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  Remote MCP Setup Guide
                </h3>
                {setupGuideOpen ? (
                  <ChevronUp className="h-5 w-5 text-gray-600" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-gray-600" />
                )}
              </div>
              <p className="mt-1 text-sm text-gray-700">
                Connect Claude Code to Kagura Memory Cloud via Remote MCP over HTTPS
              </p>
            </div>
          </button>

          {/* Collapsible Content */}
          {setupGuideOpen && (
            <div className="px-6 pb-6 border-t border-brand-green-200">
              <div className="pt-4 space-y-3 text-sm">
                <div>
                  <p className="mb-1 font-semibold text-gray-900">Add to Claude Code MCP settings:</p>
                  <pre className="overflow-x-auto rounded-lg bg-gray-900 px-3 py-2 font-mono text-xs text-green-400">
{`{
  "mcpServers": {
    "kagura-remote": {
      "type": "sse",
      "url": "https://memory.kagura-ai.com/mcp/sse",
      "headers": {
        "Authorization": "Bearer ${apiKeys[0].key_prefix}..."
      }
    }
  }
}`}
                  </pre>
                  <p className="mt-2 text-xs text-gray-600">
                    💡 Replace <code className="rounded bg-gray-200 px-1 py-0.5">{apiKeys[0].key_prefix}...</code> with your full API key shown when you created it
                  </p>
                </div>

                <div className="flex gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open('https://docs.kagura-ai.com/mcp-setup', '_blank')}
                    className="border-brand-green-300 text-brand-green-700 hover:bg-brand-green-100"
                  >
                    📚 Full Documentation
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open('https://docs.kagura-ai.com/troubleshooting', '_blank')}
                    className="border-gray-300"
                  >
                    🔧 Troubleshooting
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
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
