'use client';

/**
 * Memories Management Page
 *
 * Displays list of memories with search, filter, and CRUD operations
 * Issue #666: Phase 2 - Added Coding Sessions tab
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Search, RefreshCw, Trash2 } from 'lucide-react';
import { getMemories, bulkDeleteMemories } from '@/lib/memory';
import { listCodingSessions } from '@/lib/coding-sessions';
import type { Memory, MemoryScope } from '@/lib/types/memory';
import type { SessionSummary } from '@/lib/coding-sessions';
import { toast } from 'sonner';
import { MemoriesTable } from '@/components/memories/MemoriesTable';
import { SessionsTable } from '@/components/memories/SessionsTable';
import { CreateMemoryDialog } from '@/components/memories/CreateMemoryDialog';
import { MemoryDetailDialog } from '@/components/memories/MemoryDetailDialog';
import { SessionDetailDialog } from '@/components/memories/SessionDetailDialog';
import { EditMemoryDialog } from '@/components/memories/EditMemoryDialog';
import { DeleteMemoryDialog } from '@/components/memories/DeleteMemoryDialog';

export default function MemoriesPage() {
  const { user } = useAuth();

  // Active tab
  const [activeTab, setActiveTab] = useState<'memories' | 'sessions'>('memories');

  // Memories state
  const [memories, setMemories] = useState<Memory[]>([]);
  const [memoriesLoading, setMemoriesLoading] = useState(true);
  const [memoriesError, setMemoriesError] = useState<string | null>(null);

  // Sessions state
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [sessionsError, setSessionsError] = useState<string | null>(null);

  // Memory Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [scopeFilter, setScopeFilter] = useState<MemoryScope | 'all'>('all');
  const [agentFilter, setAgentFilter] = useState<string>('all');

  // Session Filters
  const [projectFilter, setProjectFilter] = useState<string>('all');

  // Memories Pagination
  const [memoriesPage, setMemoriesPage] = useState(1);
  const [memoriesTotal, setMemoriesTotal] = useState(0);
  const memoriesPageSize = 20;

  // Sessions Pagination
  const [sessionsPage, setSessionsPage] = useState(1);
  const [sessionsTotal, setSessionsTotal] = useState(0);
  const sessionsPageSize = 20;

  // Bulk delete (Issue #666)
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [bulkDeleting, setBulkDeleting] = useState(false);

  // Dialogs
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [detailMemory, setDetailMemory] = useState<Memory | null>(null);
  const [editMemory, setEditMemory] = useState<Memory | null>(null);
  const [deleteMemory, setDeleteMemory] = useState<Memory | null>(null);
  const [detailSessionId, setDetailSessionId] = useState<string | null>(null);

  // Fetch memories
  const fetchMemories = async () => {
    if (!user) return;

    try {
      setMemoriesLoading(true);
      setMemoriesError(null);

      const params = {
        query: searchQuery || undefined,
        scope: scopeFilter !== 'all' ? scopeFilter : undefined,
        agent_name: agentFilter !== 'all' ? agentFilter : undefined,
        limit: memoriesPageSize,
        offset: (memoriesPage - 1) * memoriesPageSize,
      };

      const response = await getMemories(params);
      setMemories(response.memories || []);
      setMemoriesTotal(response.total || 0);
    } catch (err) {
      console.error('Failed to fetch memories:', err);
      setMemoriesError(err instanceof Error ? err.message : 'Failed to load memories');
    } finally {
      setMemoriesLoading(false);
    }
  };

  // Fetch sessions
  const fetchSessions = async () => {
    if (!user) return;

    try {
      setSessionsLoading(true);
      setSessionsError(null);

      const params = {
        project_id: projectFilter !== 'all' ? projectFilter : undefined,
        limit: sessionsPageSize,
        offset: (sessionsPage - 1) * sessionsPageSize,
      };

      const response = await listCodingSessions(params);
      setSessions(response.sessions || []);
      setSessionsTotal(response.total || 0);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
      setSessionsError(err instanceof Error ? err.message : 'Failed to load sessions');
    } finally {
      setSessionsLoading(false);
    }
  };

  // Load memories on mount and filter changes
  useEffect(() => {
    if (activeTab === 'memories') {
      fetchMemories();
    }
  }, [user, memoriesPage, scopeFilter, agentFilter, activeTab]);

  // Load sessions when tab changes or filters change
  useEffect(() => {
    if (activeTab === 'sessions') {
      fetchSessions();
    }
  }, [user, sessionsPage, projectFilter, activeTab]);

  // Search with debounce (for memories only)
  useEffect(() => {
    if (activeTab !== 'memories') return;

    const timer = setTimeout(() => {
      if (memoriesPage === 1) {
        fetchMemories();
      } else {
        setMemoriesPage(1); // Reset to page 1, which will trigger fetchMemories
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery, activeTab]);

  const handleRefresh = () => {
    if (activeTab === 'memories') {
      fetchMemories();
    } else {
      fetchSessions();
    }
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

  // Handle bulk delete (Issue #666)
  const handleBulkDelete = async () => {
    if (selectedKeys.length === 0) return;

    // Confirm deletion
    if (!confirm(`Delete ${selectedKeys.length} selected memories? This action cannot be undone.`)) {
      return;
    }

    setBulkDeleting(true);
    try {
      // Parse selected keys to get actual memory keys and metadata
      // Format: "key:scope:agent_name"
      const keysToDelete = selectedKeys.map(uniqueKey => uniqueKey.split(':')[0]);

      // Group by scope (assuming all selected are from same scope for simplicity)
      // In production, you might want to handle mixed scopes
      const firstKey = selectedKeys[0];
      const scope = firstKey.split(':')[1] as 'working' | 'persistent';

      const result = await bulkDeleteMemories(keysToDelete, scope);

      if (result.deleted_count > 0) {
        toast.success(`Successfully deleted ${result.deleted_count} memories`);
      }

      if (result.failed_keys.length > 0) {
        toast.warning(`${result.failed_keys.length} memories could not be deleted`);
      }

      // Clear selection and refresh
      setSelectedKeys([]);
      fetchMemories();
    } catch (error) {
      console.error('Bulk delete failed:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to delete memories');
    } finally {
      setBulkDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Memories</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-2">
            Manage your memory cloud storage and coding sessions
          </p>
        </div>
        {activeTab === 'memories' && (
          <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Memory
          </Button>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'memories' | 'sessions')}>
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="memories">Normal Memories</TabsTrigger>
          <TabsTrigger value="sessions">Coding Sessions</TabsTrigger>
        </TabsList>

        {/* Normal Memories Tab */}
        <TabsContent value="memories" className="space-y-4 mt-6">
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
              <RefreshCw className={`h-4 w-4 ${memoriesLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>

          {/* Bulk Delete Button (Issue #666) */}
          {selectedKeys.length > 0 && (
            <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
              <span className="text-sm text-slate-700 dark:text-slate-300">
                {selectedKeys.length} {selectedKeys.length === 1 ? 'memory' : 'memories'} selected
              </span>
              <Button
                variant="destructive"
                onClick={handleBulkDelete}
                disabled={bulkDeleting}
              >
                {bulkDeleting ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Selected
                  </>
                )}
              </Button>
            </div>
          )}

          {/* Table */}
          {memoriesError ? (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
              {memoriesError}
            </div>
          ) : (
            <MemoriesTable
              memories={memories}
              loading={memoriesLoading}
              onView={(memory) => setDetailMemory(memory)}
              onEdit={(memory) => setEditMemory(memory)}
              onDelete={(memory) => setDeleteMemory(memory)}
              page={memoriesPage}
              pageSize={memoriesPageSize}
              total={memoriesTotal}
              onPageChange={setMemoriesPage}
              selectedKeys={selectedKeys}
              onSelectionChange={setSelectedKeys}
            />
          )}
        </TabsContent>

        {/* Coding Sessions Tab */}
        <TabsContent value="sessions" className="space-y-4 mt-6">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Project Filter */}
            <Select value={projectFilter} onValueChange={setProjectFilter}>
              <SelectTrigger className="w-[240px]">
                <SelectValue placeholder="All Projects" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Projects</SelectItem>
                <SelectItem value="kagura-ai">kagura-ai</SelectItem>
              </SelectContent>
            </Select>

            {/* Refresh */}
            <Button variant="outline" size="icon" onClick={handleRefresh}>
              <RefreshCw className={`h-4 w-4 ${sessionsLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>

          {/* Table */}
          {sessionsError ? (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
              {sessionsError}
            </div>
          ) : (
            <SessionsTable
              sessions={sessions}
              loading={sessionsLoading}
              onViewDetail={(session) => setDetailSessionId(session.id)}
              page={sessionsPage}
              pageSize={sessionsPageSize}
              total={sessionsTotal}
              onPageChange={setSessionsPage}
            />
          )}
        </TabsContent>
      </Tabs>

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

      {detailSessionId && (
        <SessionDetailDialog
          sessionId={detailSessionId}
          open={!!detailSessionId}
          onOpenChange={(open) => !open && setDetailSessionId(null)}
        />
      )}
    </div>
  );
}
