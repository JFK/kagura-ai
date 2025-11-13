'use client';

/**
 * Memories Management Page - Premium Redesign
 *
 * Professional design with:
 * - Grid/Table view toggle
 * - Gradient cards
 * - Modern filters
 * - Bulk actions
 * - Empty states
 */

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import {
  Plus,
  RefreshCw,
  Trash2,
  Brain,
  Code,
  Sparkles,
} from 'lucide-react';
import { getMemories, bulkDeleteMemories } from '@/lib/memory';
import { listCodingSessions } from '@/lib/coding-sessions';
import type { Memory, MemoryScope } from '@/lib/types/memory';
import type { SessionSummary } from '@/lib/coding-sessions';
import { toast } from 'sonner';

// Existing components
import { MemoriesTable } from '@/components/memories/MemoriesTable';
import { SessionsTable } from '@/components/memories/SessionsTable';
import { CreateMemoryDialog } from '@/components/memories/CreateMemoryDialog';
import { MemoryDetailDialog } from '@/components/memories/MemoryDetailDialog';
import { SessionDetailDialog } from '@/components/memories/SessionDetailDialog';
import { EditMemoryDialog } from '@/components/memories/EditMemoryDialog';
import { DeleteMemoryDialog } from '@/components/memories/DeleteMemoryDialog';

// New components
import { MemoryCard } from '@/components/memories/MemoryCard';
import { SessionCard } from '@/components/memories/SessionCard';
import { FilterBar } from '@/components/memories/FilterBar';
import { ViewToggle } from '@/components/memories/ViewToggle';
import { EmptyState } from '@/components/ui/empty-state';

export default function MemoriesPage() {
  const { user } = useAuth();

  // View mode
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

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

  // Pagination
  const [memoriesPage, setMemoriesPage] = useState(1);
  const [memoriesTotal, setMemoriesTotal] = useState(0);
  const [sessionsPage, setSessionsPage] = useState(1);
  const [sessionsTotal, setSessionsTotal] = useState(0);
  const pageSize = 20;

  // Bulk delete
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
        limit: pageSize,
        offset: (memoriesPage - 1) * pageSize,
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
        limit: pageSize,
        offset: (sessionsPage - 1) * pageSize,
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

  // Effects
  useEffect(() => {
    if (activeTab === 'memories') fetchMemories();
  }, [user, memoriesPage, scopeFilter, agentFilter, activeTab]);

  useEffect(() => {
    if (activeTab === 'sessions') fetchSessions();
  }, [user, sessionsPage, projectFilter, activeTab]);

  useEffect(() => {
    if (activeTab !== 'memories') return;
    const timer = setTimeout(() => {
      if (memoriesPage === 1) {
        fetchMemories();
      } else {
        setMemoriesPage(1);
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [searchQuery, activeTab]);

  // Handlers
  const handleRefresh = () => {
    if (activeTab === 'memories') fetchMemories();
    else fetchSessions();
  };

  const handleBulkDelete = async () => {
    if (selectedKeys.length === 0) return;
    if (!confirm(`Delete ${selectedKeys.length} memories?`)) return;

    setBulkDeleting(true);
    try {
      const keysToDelete = selectedKeys.map((uk) => uk.split(':')[0]);
      const scope = selectedKeys[0].split(':')[1] as 'working' | 'persistent';

      const result = await bulkDeleteMemories(keysToDelete, scope);
      if (result.deleted_count > 0) {
        toast.success(`Deleted ${result.deleted_count} memories`);
      }
      setSelectedKeys([]);
      fetchMemories();
    } catch (error) {
      toast.error('Failed to delete memories');
    } finally {
      setBulkDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Premium Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand-green-100 to-emerald-100 px-4 py-1.5 text-sm font-semibold text-brand-green-700">
            <Sparkles className="h-4 w-4" />
            <span>Memory Management</span>
          </div>
          <h1 className="text-4xl font-bold text-gray-900">Memories</h1>
          <p className="mt-2 text-lg text-gray-600">
            Manage your memory cloud storage and coding sessions
          </p>
        </div>

        {activeTab === 'memories' && (
          <Button
            size="lg"
            onClick={() => setCreateDialogOpen(true)}
            className="bg-gradient-to-r from-brand-green-600 to-emerald-600 text-white shadow-lg hover:from-brand-green-700 hover:to-emerald-700"
          >
            <Plus className="mr-2 h-5 w-5" />
            Create Memory
          </Button>
        )}
      </div>

      {/* Tabs with Gradient Styling */}
      <Tabs
        value={activeTab}
        onValueChange={(value) => setActiveTab(value as 'memories' | 'sessions')}
        className="space-y-6"
      >
        <div className="flex items-center justify-between">
          <TabsList className="bg-gray-100 p-1">
            <TabsTrigger
              value="memories"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-brand-green-600 data-[state=active]:to-emerald-600 data-[state=active]:text-white"
            >
              <Brain className="mr-2 h-4 w-4" />
              Normal Memories
              {memoriesTotal > 0 && (
                <Badge variant="secondary" className="ml-2 bg-white/20">
                  {memoriesTotal}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger
              value="sessions"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-brand-green-600 data-[state=active]:to-emerald-600 data-[state=active]:text-white"
            >
              <Code className="mr-2 h-4 w-4" />
              Coding Sessions
              {sessionsTotal > 0 && (
                <Badge variant="secondary" className="ml-2 bg-white/20">
                  {sessionsTotal}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          <div className="flex items-center gap-3">
            <ViewToggle value={viewMode} onChange={setViewMode} />
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={memoriesLoading || sessionsLoading}
              className="border-gray-300"
            >
              <RefreshCw
                className={`h-4 w-4 ${memoriesLoading || sessionsLoading ? 'animate-spin' : ''}`}
              />
            </Button>
          </div>
        </div>

        {/* Memories Tab */}
        <TabsContent value="memories" className="space-y-6">
          {/* Filters */}
          <FilterBar
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            searchPlaceholder="Search memories by key or value..."
            filters={[
              {
                label: 'Scope',
                value: scopeFilter,
                options: [
                  { value: 'all', label: 'All Scopes' },
                  { value: 'working', label: 'Working' },
                  { value: 'persistent', label: 'Persistent' },
                ],
                onChange: (v) => setScopeFilter(v as MemoryScope | 'all'),
              },
              {
                label: 'Agent',
                value: agentFilter,
                options: [
                  { value: 'all', label: 'All Agents' },
                  // Add more agent options as needed
                ],
                onChange: setAgentFilter,
              },
            ]}
          />

          {/* Bulk Actions */}
          {selectedKeys.length > 0 && (
            <div className="flex items-center justify-between rounded-lg border-2 border-brand-green-300 bg-brand-green-50 p-4">
              <span className="text-sm font-medium text-gray-900">
                {selectedKeys.length} selected
              </span>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleBulkDelete}
                disabled={bulkDeleting}
                className="bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-700 hover:to-rose-700"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete Selected
              </Button>
            </div>
          )}

          {/* Content */}
          {memoriesLoading ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-64 animate-pulse rounded-2xl bg-gradient-to-br from-gray-100 to-gray-200" />
              ))}
            </div>
          ) : memoriesError ? (
            <div className="rounded-2xl border-2 border-red-200 bg-red-50 p-8 text-center">
              <p className="text-red-600">{memoriesError}</p>
            </div>
          ) : memories.length === 0 ? (
            <EmptyState
              emoji="🧠"
              title="No memories found"
              description="Create your first memory to get started, or adjust your search filters."
              actionLabel="Create Memory"
              onAction={() => setCreateDialogOpen(true)}
            />
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {memories.map((memory) => (
                <MemoryCard
                  key={`${memory.key}:${memory.scope}:${memory.agent_name}`}
                  memory={memory}
                  onView={setDetailMemory}
                  onEdit={setEditMemory}
                  onDelete={setDeleteMemory}
                />
              ))}
            </div>
          ) : (
            <MemoriesTable
              memories={memories}
              selectedKeys={selectedKeys}
              onSelectionChange={setSelectedKeys}
              onView={setDetailMemory}
              onEdit={setEditMemory}
              onDelete={setDeleteMemory}
              loading={memoriesLoading}
              page={memoriesPage}
              pageSize={pageSize}
              total={memoriesTotal}
              onPageChange={setMemoriesPage}
            />
          )}

          {/* Pagination */}
          {memoriesTotal > pageSize && (
            <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4">
              <p className="text-sm text-gray-600">
                Showing {(memoriesPage - 1) * pageSize + 1}-
                {Math.min(memoriesPage * pageSize, memoriesTotal)} of {memoriesTotal}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setMemoriesPage((p) => Math.max(1, p - 1))}
                  disabled={memoriesPage === 1}
                  className="border-gray-300"
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setMemoriesPage((p) => p + 1)}
                  disabled={memoriesPage * pageSize >= memoriesTotal}
                  className="border-gray-300"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </TabsContent>

        {/* Sessions Tab */}
        <TabsContent value="sessions" className="space-y-6">
          {/* Filters */}
          <FilterBar
            searchQuery=""
            onSearchChange={() => {}}
            searchPlaceholder="Search sessions..."
            filters={[
              {
                label: 'Project',
                value: projectFilter,
                options: [{ value: 'all', label: 'All Projects' }],
                onChange: setProjectFilter,
              },
            ]}
          />

          {/* Content */}
          {sessionsLoading ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-80 animate-pulse rounded-2xl bg-gradient-to-br from-gray-100 to-gray-200" />
              ))}
            </div>
          ) : sessionsError ? (
            <div className="rounded-2xl border-2 border-red-200 bg-red-50 p-8 text-center">
              <p className="text-red-600">{sessionsError}</p>
            </div>
          ) : sessions.length === 0 ? (
            <EmptyState
              emoji="💻"
              title="No coding sessions found"
              description="Start a coding session to track your development workflow."
              actionLabel="Learn More"
              onAction={() => window.open('https://docs.kagura-ai.com', '_blank')}
            />
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {sessions.map((session) => (
                <SessionCard
                  key={session.id}
                  session={session}
                  onView={setDetailSessionId}
                />
              ))}
            </div>
          ) : (
            <SessionsTable
              sessions={sessions}
              onViewDetail={(session) => setDetailSessionId(session.id)}
              loading={sessionsLoading}
              page={sessionsPage}
              pageSize={pageSize}
              total={sessionsTotal}
              onPageChange={setSessionsPage}
            />
          )}

          {/* Pagination */}
          {sessionsTotal > pageSize && (
            <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4">
              <p className="text-sm text-gray-600">
                Showing {(sessionsPage - 1) * pageSize + 1}-
                {Math.min(sessionsPage * pageSize, sessionsTotal)} of {sessionsTotal}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSessionsPage((p) => Math.max(1, p - 1))}
                  disabled={sessionsPage === 1}
                  className="border-gray-300"
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSessionsPage((p) => p + 1)}
                  disabled={sessionsPage * pageSize >= sessionsTotal}
                  className="border-gray-300"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <CreateMemoryDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSuccess={() => {
          setCreateDialogOpen(false);
          fetchMemories();
        }}
      />

      {detailMemory && (
        <MemoryDetailDialog
          memory={detailMemory}
          open={true}
          onOpenChange={(open) => !open && setDetailMemory(null)}
          onEdit={() => {
            const mem = detailMemory;
            setDetailMemory(null);
            setEditMemory(mem);
          }}
          onDelete={() => {
            const mem = detailMemory;
            setDetailMemory(null);
            setDeleteMemory(mem);
          }}
        />
      )}

      {editMemory && (
        <EditMemoryDialog
          memory={editMemory}
          open={true}
          onOpenChange={(open) => !open && setEditMemory(null)}
          onSuccess={() => {
            setEditMemory(null);
            fetchMemories();
          }}
        />
      )}

      {deleteMemory && (
        <DeleteMemoryDialog
          memory={deleteMemory}
          open={true}
          onOpenChange={(open) => !open && setDeleteMemory(null)}
          onSuccess={() => {
            setDeleteMemory(null);
            fetchMemories();
          }}
        />
      )}

      {detailSessionId && (
        <SessionDetailDialog
          sessionId={detailSessionId}
          open={true}
          onOpenChange={(open) => !open && setDetailSessionId(null)}
        />
      )}
    </div>
  );
}
