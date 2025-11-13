'use client';

/**
 * Memories Management Page
 *
 * Displays list of memories with search, filter, and CRUD operations
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
import { Plus, Search, RefreshCw } from 'lucide-react';
import { getMemories } from '@/lib/memory';
import type { Memory, MemoryScope } from '@/lib/types/memory';
import { MemoriesTable } from '@/components/memories/MemoriesTable';
import { CreateMemoryDialog } from '@/components/memories/CreateMemoryDialog';
import { MemoryDetailDialog } from '@/components/memories/MemoryDetailDialog';
import { EditMemoryDialog } from '@/components/memories/EditMemoryDialog';
import { DeleteMemoryDialog } from '@/components/memories/DeleteMemoryDialog';

export default function MemoriesPage() {
  const { user } = useAuth();
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [scopeFilter, setScopeFilter] = useState<MemoryScope | 'all'>('all');
  const [agentFilter, setAgentFilter] = useState<string>('all');

  // Pagination
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  // Dialogs
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [detailMemory, setDetailMemory] = useState<Memory | null>(null);
  const [editMemory, setEditMemory] = useState<Memory | null>(null);
  const [deleteMemory, setDeleteMemory] = useState<Memory | null>(null);

  // Fetch memories
  const fetchMemories = async () => {
    if (!user) return;

    try {
      setLoading(true);
      setError(null);

      const params = {
        query: searchQuery || undefined,
        scope: scopeFilter !== 'all' ? scopeFilter : undefined,
        agent_name: agentFilter !== 'all' ? agentFilter : undefined,
        limit: pageSize,
        offset: (page - 1) * pageSize,
      };

      const response = await getMemories(params);
      setMemories(response.memories || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error('Failed to fetch memories:', err);
      setError(err instanceof Error ? err.message : 'Failed to load memories');
    } finally {
      setLoading(false);
    }
  };

  // Load memories on mount and filter changes
  useEffect(() => {
    fetchMemories();
  }, [user, page, scopeFilter, agentFilter]);

  // Search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (page === 1) {
        fetchMemories();
      } else {
        setPage(1); // Reset to page 1, which will trigger fetchMemories
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleRefresh = () => {
    fetchMemories();
  };

  const handleMemoryCreated = () => {
    setCreateDialogOpen(false);
    fetchMemories();
  };

  const handleMemoryUpdated = () => {
    setEditMemory(null);
    fetchMemories();
  };

  const handleMemoryDeleted = () => {
    setDeleteMemory(null);
    fetchMemories();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Memories</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-2">
            Manage your memory cloud storage
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Memory
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Scope Filter */}
        <Select value={scopeFilter} onValueChange={(value) => setScopeFilter(value as MemoryScope | 'all')}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Scopes" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Scopes</SelectItem>
            <SelectItem value="working">Working</SelectItem>
            <SelectItem value="persistent">Persistent</SelectItem>
          </SelectContent>
        </Select>

        {/* Agent Filter */}
        <Select value={agentFilter} onValueChange={setAgentFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Agents" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Agents</SelectItem>
            <SelectItem value="global">Global</SelectItem>
            <SelectItem value="chatbot">Chatbot</SelectItem>
            <SelectItem value="translator">Translator</SelectItem>
          </SelectContent>
        </Select>

        {/* Refresh */}
        <Button variant="outline" size="icon" onClick={handleRefresh}>
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Table */}
      {error ? (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
          {error}
        </div>
      ) : (
        <MemoriesTable
          memories={memories}
          loading={loading}
          onView={(memory) => setDetailMemory(memory)}
          onEdit={(memory) => setEditMemory(memory)}
          onDelete={(memory) => setDeleteMemory(memory)}
          page={page}
          pageSize={pageSize}
          total={total}
          onPageChange={setPage}
        />
      )}

      {/* Dialogs */}
      <CreateMemoryDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSuccess={handleMemoryCreated}
      />

      {detailMemory && (
        <MemoryDetailDialog
          memory={detailMemory}
          open={!!detailMemory}
          onOpenChange={(open) => !open && setDetailMemory(null)}
          onEdit={() => {
            setEditMemory(detailMemory);
            setDetailMemory(null);
          }}
          onDelete={() => {
            setDeleteMemory(detailMemory);
            setDetailMemory(null);
          }}
        />
      )}

      {editMemory && (
        <EditMemoryDialog
          memory={editMemory}
          open={!!editMemory}
          onOpenChange={(open) => !open && setEditMemory(null)}
          onSuccess={handleMemoryUpdated}
        />
      )}

      {deleteMemory && (
        <DeleteMemoryDialog
          memory={deleteMemory}
          open={!!deleteMemory}
          onOpenChange={(open) => !open && setDeleteMemory(null)}
          onSuccess={handleMemoryDeleted}
        />
      )}
    </div>
  );
}
