'use client';

/**
 * App Credentials (OAuth2 Clients) Management Page
 *
 * Issue #684 - OAuth2 Client Applications Management
 * Full CRUD implementation for ChatGPT Apps, Claude Connectors, etc.
 */

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Plus,
  RefreshCw,
  AlertCircle,
  Puzzle,
  Trash2,
  Edit,
  Copy,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react';
import {
  getOAuth2Clients,
  createOAuth2Client,
  updateOAuth2Client,
  deleteOAuth2Client,
  type OAuth2Client,
  type OAuth2ClientCreateRequest,
  type OAuth2ClientWithSecret,
} from '@/lib/oauth';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';

export default function AppCredentialsPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [clients, setClients] = useState<OAuth2Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createData, setCreateData] = useState({
    client_name: '',
    redirect_uris: '',
    scope: 'openid profile email',
  });
  const [createdSecret, setCreatedSecret] = useState<string | null>(null);

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingClient, setEditingClient] = useState<OAuth2Client | null>(null);
  const [updating, setUpdating] = useState(false);

  // Setup guide state
  const [showGuide, setShowGuide] = useState(false);

  // Fetch OAuth2 clients
  const fetchClients = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await getOAuth2Clients();
      setClients(data || []);
    } catch (err) {
      console.error('Failed to fetch OAuth2 clients:', err);
      setError(err instanceof Error ? err.message : 'Failed to load OAuth2 clients');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  // Handle create client
  const handleCreate = async () => {
    if (!createData.client_name.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Client name is required',
        variant: 'destructive',
      });
      return;
    }

    if (!createData.redirect_uris.trim()) {
      toast({
        title: 'Validation Error',
        description: 'At least one redirect URI is required',
        variant: 'destructive',
      });
      return;
    }

    try {
      setCreating(true);

      const redirectUris = createData.redirect_uris
        .split('\n')
        .map((uri) => uri.trim())
        .filter((uri) => uri.length > 0);

      const payload: OAuth2ClientCreateRequest = {
        client_name: createData.client_name.trim(),
        redirect_uris: redirectUris,
        scope: createData.scope.trim(),
        grant_types: ['authorization_code', 'refresh_token'],
        response_types: ['code'],
        token_endpoint_auth_method: 'client_secret_basic',
      };

      const result: OAuth2ClientWithSecret = await createOAuth2Client(payload);

      // Show client secret (one-time display)
      setCreatedSecret(result.client_secret);

      // Refresh list
      await fetchClients();

      toast({
        title: 'Client Created',
        description: `${result.client_name} has been created successfully.`,
      });

      // Reset form but keep modal open to show secret
      setCreateData({
        client_name: '',
        redirect_uris: '',
        scope: 'openid profile email',
      });
    } catch (err) {
      console.error('Failed to create client:', err);
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to create client',
        variant: 'destructive',
      });
    } finally {
      setCreating(false);
    }
  };

  // Handle edit client
  const handleEdit = async (client: OAuth2Client) => {
    setEditingClient(client);
    setShowEditModal(true);
  };

  const handleUpdate = async () => {
    if (!editingClient) return;

    try {
      setUpdating(true);

      const payload = {
        client_name: editingClient.client_name,
        redirect_uris: editingClient.redirect_uris,
        scope: editingClient.scope,
      };

      await updateOAuth2Client(editingClient.client_id, payload);

      // Refresh list
      await fetchClients();

      toast({
        title: 'Client Updated',
        description: `${editingClient.client_name} has been updated successfully.`,
      });

      setShowEditModal(false);
      setEditingClient(null);
    } catch (err) {
      console.error('Failed to update client:', err);
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to update client',
        variant: 'destructive',
      });
    } finally {
      setUpdating(false);
    }
  };

  // Handle delete
  const handleDelete = async (client: OAuth2Client) => {
    if (!confirm(`Delete ${client.client_name}? This action cannot be undone.`)) {
      return;
    }

    try {
      await deleteOAuth2Client(client.client_id);

      toast({
        title: 'Client Deleted',
        description: `${client.client_name} has been deleted.`,
      });

      // Refresh list
      await fetchClients();
    } catch (err) {
      console.error('Failed to delete client:', err);
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to delete client',
        variant: 'destructive',
      });
    }
  };

  // Copy to clipboard
  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied',
      description: `${label} copied to clipboard`,
    });
  };

  // Close create modal
  const closeCreateModal = () => {
    setShowCreateModal(false);
    setCreatedSecret(null);
    setCreateData({
      client_name: '',
      redirect_uris: '',
      scope: 'openid profile email',
    });
  };

  return (
    <div className="p-8 space-y-6">
      {/* Premium Header (Matching api-keys style) */}
      <div className="flex items-start justify-between">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand-green-100 to-emerald-100 px-4 py-1.5 text-sm font-semibold text-brand-green-700">
            <Puzzle className="h-4 w-4" />
            <span>Integration Management</span>
          </div>
          <h1 className="text-4xl font-bold text-gray-900">App Credentials</h1>
          <p className="mt-2 text-lg text-gray-600">
            Manage OAuth2 client applications (ChatGPT Apps, Claude Connectors, etc.)
          </p>
        </div>

        <div className="flex gap-2">
          <Button onClick={fetchClients} variant="outline" disabled={loading} size="lg" className="shadow-sm">
            <RefreshCw className={`h-5 w-5 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            size="lg"
            onClick={() => setShowCreateModal(true)}
            className="bg-gradient-to-r from-brand-green-600 to-emerald-600 text-white shadow-lg hover:from-brand-green-700 hover:to-emerald-700"
          >
            <Plus className="mr-2 h-5 w-5" />
            Add OAuth2 Client
          </Button>
        </div>
      </div>

      {/* Setup Guide (Matching api-keys style) */}
      <div className="rounded-2xl border-2 border-brand-green-200 bg-gradient-to-br from-brand-green-50 to-emerald-50">
        {/* Collapsible Header */}
        <button
          onClick={() => setShowGuide(!showGuide)}
          className="w-full p-6 flex items-start gap-4 hover:bg-brand-green-100/50 transition-colors rounded-t-2xl text-left"
        >
          <div className="flex-shrink-0 rounded-lg bg-brand-green-600 p-3 text-white">
            <Info className="h-6 w-6" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">
                OAuth2 Setup Guide
              </h3>
              {showGuide ? (
                <ChevronUp className="h-5 w-5 text-gray-600" />
              ) : (
                <ChevronDown className="h-5 w-5 text-gray-600" />
              )}
            </div>
            <p className="mt-1 text-sm text-gray-700">
              Configure OAuth2 clients for ChatGPT Apps, Claude Desktop, etc.
            </p>
          </div>
        </button>

        {/* Content */}
        {showGuide && (
          <div className="px-6 pb-6 border-t border-brand-green-200 space-y-4">
            <div className="space-y-2 mt-4">
              <h3 className="font-semibold text-sm text-gray-900">For ChatGPT Apps:</h3>
              <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700 ml-2">
                <li>Create OAuth2 client with redirect URI: <code className="text-xs bg-white px-2 py-0.5 rounded border border-brand-green-200">https://chat.openai.com/aip/oauth/callback</code></li>
                <li>Copy Client ID and Client Secret</li>
                <li>In ChatGPT settings, configure OAuth2 with these credentials</li>
                <li>Set Authorization URL: <code className="text-xs bg-white px-2 py-0.5 rounded border border-brand-green-200">{typeof window !== 'undefined' ? window.location.origin : ''}/auth/oauth2/authorize</code></li>
                <li>Set Token URL: <code className="text-xs bg-white px-2 py-0.5 rounded border border-brand-green-200">{typeof window !== 'undefined' ? window.location.origin : ''}/auth/oauth2/token</code></li>
              </ol>
            </div>

            <div className="space-y-2">
              <h3 className="font-semibold text-sm text-gray-900">For Claude Desktop:</h3>
              <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700 ml-2">
                <li>Create OAuth2 client with redirect URI: <code className="text-xs bg-white px-2 py-0.5 rounded border border-brand-green-200">http://localhost:3000/callback</code></li>
                <li>Edit Claude Desktop config file (<code className="bg-white px-2 py-0.5 rounded border border-brand-green-200">~/.config/claude/config.json</code>)</li>
                <li>Add MCP server with OAuth2 authentication</li>
                <li>Use Client ID and Client Secret from created client</li>
              </ol>
            </div>
          </div>
        )}
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Clients Table */}
      <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>App Name</TableHead>
              <TableHead>Client ID</TableHead>
              <TableHead>Redirect URIs</TableHead>
              <TableHead>Scope</TableHead>
              <TableHead>Grant Types</TableHead>
              <TableHead>Created At</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  <div className="flex items-center justify-center gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-slate-500">Loading clients...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : clients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  <Puzzle className="h-12 w-12 text-slate-300 mx-auto mb-2" />
                  <p className="text-sm text-slate-500">No OAuth2 clients registered yet</p>
                  <p className="text-xs text-slate-400 mt-1">
                    Click "Add OAuth2 Client" to create your first client
                  </p>
                </TableCell>
              </TableRow>
            ) : (
              clients.map((client) => (
                <TableRow key={client.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Puzzle className="h-4 w-4 text-slate-400" />
                      <span className="font-medium">{client.client_name}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <code className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                        {client.client_id.substring(0, 12)}...
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => copyToClipboard(client.client_id, 'Client ID')}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="max-w-xs space-y-1">
                      {client.redirect_uris.map((uri, idx) => (
                        <div key={idx} className="text-xs text-slate-600 dark:text-slate-400 truncate">
                          {uri}
                        </div>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1 max-w-[200px]">
                      {client.scope.split(' ').slice(0, 3).map((scope) => (
                        <Badge key={scope} variant="outline" className="text-xs">
                          {scope}
                        </Badge>
                      ))}
                      {client.scope.split(' ').length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{client.scope.split(' ').length - 3}
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {client.grant_types.map((type) => (
                        <Badge key={type} variant="secondary" className="text-xs">
                          {type}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-xs text-slate-600 dark:text-slate-400">
                      {new Date(client.created_at).toLocaleDateString()}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={() => handleEdit(client)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={() => handleDelete(client)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Create Client Modal */}
      <Dialog open={showCreateModal} onOpenChange={closeCreateModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add OAuth2 Client</DialogTitle>
            <DialogDescription>
              Create a new OAuth2 client for ChatGPT Apps, Claude Desktop, or other applications
            </DialogDescription>
          </DialogHeader>

          {createdSecret ? (
            // Show created secret (one-time display)
            <div className="space-y-4">
              <Alert>
                <CheckCircle className="h-4 w-4 text-green-500" />
                <AlertTitle>Client Created Successfully!</AlertTitle>
                <AlertDescription>
                  <div className="mt-2 space-y-3">
                    <p className="text-sm font-medium">
                      Save the Client Secret now. You won't be able to see it again!
                    </p>

                    <div className="space-y-2">
                      <Label>Client Secret</Label>
                      <div className="flex gap-2">
                        <Input
                          value={createdSecret}
                          readOnly
                          className="font-mono text-sm"
                        />
                        <Button
                          variant="outline"
                          onClick={() => copyToClipboard(createdSecret, 'Client Secret')}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    <p className="text-xs text-slate-500 mt-2">
                      Store this secret securely. You'll need it to configure your OAuth2 application.
                    </p>
                  </div>
                </AlertDescription>
              </Alert>
            </div>
          ) : (
            // Create form
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="client_name">
                  Client Name <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="client_name"
                  value={createData.client_name}
                  onChange={(e) =>
                    setCreateData({ ...createData, client_name: e.target.value })
                  }
                  placeholder="e.g., ChatGPT Connector, Claude Desktop"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="redirect_uris">
                  Redirect URIs <span className="text-red-500">*</span>
                </Label>
                <Textarea
                  id="redirect_uris"
                  value={createData.redirect_uris}
                  onChange={(e) =>
                    setCreateData({ ...createData, redirect_uris: e.target.value })
                  }
                  placeholder="https://chat.openai.com/aip/oauth/callback&#10;http://localhost:3000/callback"
                  rows={4}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-slate-500">
                  Enter one URI per line. These are the allowed callback URLs for your application.
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="scope">Scope</Label>
                <Input
                  id="scope"
                  value={createData.scope}
                  onChange={(e) => setCreateData({ ...createData, scope: e.target.value })}
                  placeholder="openid profile email"
                />
                <p className="text-xs text-slate-500">
                  Space-separated list of OAuth2 scopes. Default is sufficient for most cases.
                </p>
              </div>
            </div>
          )}

          <DialogFooter>
            {createdSecret ? (
              <Button onClick={closeCreateModal}>Done</Button>
            ) : (
              <>
                <Button variant="outline" onClick={closeCreateModal}>
                  Cancel
                </Button>
                <Button onClick={handleCreate} disabled={creating}>
                  {creating ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Client'
                  )}
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Client Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit OAuth2 Client</DialogTitle>
            <DialogDescription>
              Update client name, redirect URIs, and scope. Client Secret cannot be changed.
            </DialogDescription>
          </DialogHeader>

          {editingClient && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="edit_client_name">Client Name</Label>
                <Input
                  id="edit_client_name"
                  value={editingClient.client_name}
                  onChange={(e) =>
                    setEditingClient({ ...editingClient, client_name: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit_redirect_uris">Redirect URIs</Label>
                <Textarea
                  id="edit_redirect_uris"
                  value={editingClient.redirect_uris.join('\n')}
                  onChange={(e) => {
                    const uris = e.target.value
                      .split('\n')
                      .map((uri) => uri.trim())
                      .filter((uri) => uri.length > 0);
                    setEditingClient({ ...editingClient, redirect_uris: uris.length > 0 ? uris : [''] });
                  }}
                  rows={4}
                  className="font-mono text-sm"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit_scope">Scope</Label>
                <Input
                  id="edit_scope"
                  value={editingClient.scope}
                  onChange={(e) =>
                    setEditingClient({ ...editingClient, scope: e.target.value })
                  }
                />
              </div>

              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  <strong>Note:</strong> Client ID and Client Secret cannot be changed for security
                  reasons. If you need different credentials, create a new client.
                </AlertDescription>
              </Alert>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdate} disabled={updating}>
              {updating ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                'Update Client'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
