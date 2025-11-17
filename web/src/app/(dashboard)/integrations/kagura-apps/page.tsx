'use client';

/**
 * Kagura Apps (MCP Clients) Management Page
 *
 * Issue #684 - OAuth2 Client Applications Management
 * Displays registered OAuth2 client applications (ChatGPT, Claude Desktop, etc.)
 * with CRUD operations
 */

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Plus, RefreshCw, AlertCircle, Puzzle, Trash2, Edit } from 'lucide-react';
import {
  getOAuth2Clients,
  deleteOAuth2Client,
  type OAuth2Client,
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
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

export default function KaguraAppsPage() {
  const { user } = useAuth();
  const [clients, setClients] = useState<OAuth2Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteClient, setDeleteClient] = useState<OAuth2Client | null>(null);
  const [deleting, setDeleting] = useState(false);

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

  // Handle delete
  const handleDelete = async () => {
    if (!deleteClient) return;

    try {
      setDeleting(true);
      await deleteOAuth2Client(deleteClient.client_id);

      // Refresh list
      await fetchClients();
      setDeleteClient(null);
    } catch (err) {
      console.error('Failed to delete client:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete client');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Kagura Apps (OAuth2 Clients)
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Manage OAuth2 client applications connected to Kagura AI
          </p>
        </div>

        <div className="flex gap-2">
          <Button
            onClick={fetchClients}
            variant="outline"
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
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

      {/* Clients Table */}
      <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>App Name</TableHead>
              <TableHead>Client ID</TableHead>
              <TableHead>Redirect URIs</TableHead>
              <TableHead>Scope</TableHead>
              <TableHead>Created At</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  <div className="flex items-center justify-center gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-slate-500">Loading clients...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : clients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  <Puzzle className="h-12 w-12 text-slate-300 mx-auto mb-2" />
                  <p className="text-sm text-slate-500">
                    No OAuth2 clients registered yet
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Register a client application to enable OAuth2 authentication
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
                    <code className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                      {client.client_id}
                    </code>
                  </TableCell>
                  <TableCell>
                    <div className="max-w-xs">
                      {client.redirect_uris.map((uri, idx) => (
                        <div key={idx} className="text-xs text-slate-600 dark:text-slate-400 truncate">
                          {uri}
                        </div>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {client.scope.split(' ').map((scope) => (
                        <Badge key={scope} variant="outline" className="text-xs">
                          {scope}
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
                        onClick={() => setDeleteClient(client)}
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

      {/* Info Alert */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>About OAuth2 Clients</AlertTitle>
        <AlertDescription>
          <div className="mt-2 space-y-2 text-sm">
            <p>
              OAuth2 clients are applications that can authenticate with Kagura AI using OAuth2 protocol.
            </p>
            <p className="font-medium">Currently registered:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li><strong>ChatGPT Connector</strong> - Allows ChatGPT to access Kagura MCP server</li>
              <li><strong>Claude Desktop</strong> - Allows Claude Desktop to authenticate with Kagura</li>
            </ul>
            <p className="mt-2 text-xs text-slate-500">
              To register new clients, use the API or contact an administrator.
            </p>
          </div>
        </AlertDescription>
      </Alert>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteClient} onOpenChange={(open) => !open && setDeleteClient(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete OAuth2 Client</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete <strong>{deleteClient?.client_name}</strong>?
              This action cannot be undone. All associated tokens will be revoked.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-red-500 hover:bg-red-600"
            >
              {deleting ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
