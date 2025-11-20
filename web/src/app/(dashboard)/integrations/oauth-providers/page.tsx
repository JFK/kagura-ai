'use client';

/**
 * OAuth2 Providers Settings Page
 *
 * Issue #684 - OAuth2 Provider Configuration UI
 * Full .env.cloud integration for editing OAuth provider credentials
 */

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Plus,
  RefreshCw,
  AlertCircle,
  Shield,
  CheckCircle2,
  XCircle,
  Edit,
  Save,
  Eye,
  EyeOff,
} from 'lucide-react';
import { getOAuth2Providers } from '@/lib/oauth';
import { getConfig, batchUpdateConfig, validateConfig } from '@/lib/config';
import type { OAuth2Provider } from '@/lib/oauth';
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';

interface ProviderConfig {
  client_id: string;
  client_secret: string;
}

export default function OAuthProvidersPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [providers, setProviders] = useState<OAuth2Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingProvider, setEditingProvider] = useState<string | null>(null);
  const [editData, setEditData] = useState<ProviderConfig>({
    client_id: '',
    client_secret: '',
  });
  const [showSecret, setShowSecret] = useState(false);
  const [saving, setSaving] = useState(false);

  const isAdmin = user?.role === 'admin';

  // Fetch OAuth2 providers
  const fetchProviders = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await getOAuth2Providers();
      setProviders(data || []);
    } catch (err) {
      console.error('Failed to fetch OAuth2 providers:', err);
      setError(err instanceof Error ? err.message : 'Failed to load OAuth2 providers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProviders();
  }, []);

  // Handle edit provider
  const handleEditProvider = async (providerName: string) => {
    try {
      // Fetch current config from .env.cloud
      const config = await getConfig(true); // mask_sensitive=true

      const clientIdKey = `${providerName.toUpperCase()}_CLIENT_ID`;
      const clientSecretKey = `${providerName.toUpperCase()}_CLIENT_SECRET`;

      setEditData({
        client_id: config.config[clientIdKey] || '',
        client_secret: config.config[clientSecretKey] || '',
      });

      setEditingProvider(providerName);
      setShowEditModal(true);
      setShowSecret(false);
    } catch (err) {
      console.error('Failed to load provider config:', err);
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to load configuration',
        variant: 'destructive',
      });
    }
  };

  // Handle save provider config
  const handleSaveProvider = async () => {
    if (!editingProvider) return;

    // Validation
    if (!editData.client_id.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Client ID is required',
        variant: 'destructive',
      });
      return;
    }

    if (!editData.client_secret.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Client Secret is required',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);

      const clientIdKey = `${editingProvider.toUpperCase()}_CLIENT_ID`;
      const clientSecretKey = `${editingProvider.toUpperCase()}_CLIENT_SECRET`;

      const updates = {
        [clientIdKey]: editData.client_id.trim(),
        [clientSecretKey]: editData.client_secret.trim(),
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
        return;
      }

      // Save to .env.cloud
      await batchUpdateConfig(updates);

      toast({
        title: 'Configuration Saved',
        description: `${editingProvider} OAuth credentials have been updated in .env.cloud`,
      });

      // Show restart warning
      toast({
        title: 'Application Restart Required',
        description: 'Please restart the API container for changes to take effect.',
        variant: 'default',
      });

      // Refresh providers list
      await fetchProviders();

      setShowEditModal(false);
      setEditingProvider(null);
    } catch (err) {
      console.error('Failed to save provider config:', err);
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to save configuration',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  // Non-admin view
  if (!isAdmin) {
    return (
      <div className="p-8">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Admin Access Required</AlertTitle>
          <AlertDescription>
            OAuth2 provider configuration is only available to administrators.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">OAuth2 Providers</h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Configure OAuth2 authentication providers (Google, GitHub, Microsoft)
          </p>
        </div>

        <Button onClick={fetchProviders} variant="outline" disabled={loading}>
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

      {/* Providers Table */}
      <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Provider</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Client ID</TableHead>
              <TableHead>Scopes</TableHead>
              <TableHead>Authorization URL</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  <div className="flex items-center justify-center gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-slate-500">Loading providers...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : providers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  <p className="text-sm text-slate-500">No OAuth2 providers configured</p>
                </TableCell>
              </TableRow>
            ) : (
              providers.map((provider) => (
                <TableRow key={provider.name}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-slate-400" />
                      <span className="font-medium">{provider.display_name}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {provider.configured ? (
                      <Badge variant="default" className="bg-green-500">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Configured
                      </Badge>
                    ) : (
                      <Badge variant="secondary">
                        <XCircle className="h-3 w-3 mr-1" />
                        Not Configured
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    {provider.client_id ? (
                      <code className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                        {provider.client_id.substring(0, 20)}...
                      </code>
                    ) : (
                      <span className="text-xs text-slate-400">Not set</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1 max-w-[200px]">
                      {provider.scopes.slice(0, 3).map((scope) => (
                        <Badge key={scope} variant="outline" className="text-xs">
                          {scope}
                        </Badge>
                      ))}
                      {provider.scopes.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{provider.scopes.length - 3}
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <a
                      href={provider.authorization_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:underline truncate block max-w-[200px]"
                    >
                      {provider.authorization_url}
                    </a>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={() => handleEditProvider(provider.name)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Configuration Guide */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>How to Configure OAuth2 Providers</AlertTitle>
        <AlertDescription>
          <div className="mt-2 space-y-2 text-sm">
            <p>
              Click "Edit" to configure OAuth2 credentials for each provider. Credentials are stored
              in <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">.env.cloud</code>.
            </p>
            <p className="mt-2">
              <strong>Important:</strong> After saving changes, you must restart the API container:
            </p>
            <code className="block bg-slate-100 dark:bg-slate-900 px-3 py-2 rounded text-xs mt-2">
              docker-compose restart api
            </code>
            <p className="mt-2 text-xs text-slate-500">
              Get OAuth2 credentials from provider dashboards:
            </p>
            <ul className="list-disc list-inside space-y-1 ml-2 text-xs">
              <li>
                <strong>Google</strong>:{' '}
                <a
                  href="https://console.cloud.google.com/apis/credentials"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  Google Cloud Console
                </a>
              </li>
              <li>
                <strong>GitHub</strong>:{' '}
                <a
                  href="https://github.com/settings/developers"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  GitHub Developer Settings
                </a>
              </li>
              <li>
                <strong>Microsoft</strong>:{' '}
                <a
                  href="https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  Azure App Registrations
                </a>
              </li>
            </ul>
          </div>
        </AlertDescription>
      </Alert>

      {/* Edit Provider Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit {editingProvider?.toUpperCase()} OAuth2 Configuration</DialogTitle>
            <DialogDescription>
              Update OAuth2 client credentials for {editingProvider}. Changes will be saved to .env.cloud.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="client_id">
                Client ID <span className="text-red-500">*</span>
              </Label>
              <Input
                id="client_id"
                value={editData.client_id}
                onChange={(e) => setEditData({ ...editData, client_id: e.target.value })}
                placeholder="Enter client ID"
                className="font-mono text-sm"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="client_secret">
                Client Secret <span className="text-red-500">*</span>
              </Label>
              <div className="flex gap-2">
                <Input
                  id="client_secret"
                  type={showSecret ? 'text' : 'password'}
                  value={editData.client_secret}
                  onChange={(e) => setEditData({ ...editData, client_secret: e.target.value })}
                  placeholder="Enter client secret"
                  className="font-mono text-sm"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setShowSecret(!showSecret)}
                >
                  {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-xs text-slate-500">
                Existing values are masked. Enter new value to update.
              </p>
            </div>

            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-xs">
                <strong>Note:</strong> After saving, you must restart the API container for changes to take effect:
                <code className="block bg-slate-100 dark:bg-slate-900 px-2 py-1 rounded mt-1">
                  docker-compose restart api
                </code>
              </AlertDescription>
            </Alert>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveProvider} disabled={saving}>
              {saving ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save to .env.cloud
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
