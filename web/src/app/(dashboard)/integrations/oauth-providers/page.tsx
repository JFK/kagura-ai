'use client';

/**
 * OAuth2 Providers Settings Page
 *
 * Issue #684 - OAuth2 Provider Configuration UI
 * Displays configured OAuth2 providers (Google, GitHub) and allows client registration
 */

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Plus, RefreshCw, AlertCircle, Shield, CheckCircle2, XCircle } from 'lucide-react';
import { getOAuth2Providers } from '@/lib/oauth';
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

export default function OAuthProvidersPage() {
  const { user } = useAuth();
  const [providers, setProviders] = useState<OAuth2Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            OAuth2 Providers
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Configure OAuth2 authentication providers (Google, GitHub, etc.)
          </p>
        </div>

        <Button
          onClick={fetchProviders}
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
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8">
                  <div className="flex items-center justify-center gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-slate-500">Loading providers...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : providers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8">
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
                    <code className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                      {provider.client_id || 'Not set'}
                    </code>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {provider.scopes.map((scope) => (
                        <Badge key={scope} variant="outline" className="text-xs">
                          {scope}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <a
                      href={provider.authorization_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:underline"
                    >
                      {provider.authorization_url}
                    </a>
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
            <p>Set these environment variables in <code>.env.cloud</code>:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>
                <strong>Google</strong>: <code>GOOGLE_CLIENT_ID</code>, <code>GOOGLE_CLIENT_SECRET</code>
              </li>
              <li>
                <strong>GitHub</strong>: <code>GITHUB_CLIENT_ID</code>, <code>GITHUB_CLIENT_SECRET</code> (not yet supported)
              </li>
            </ul>
            <p className="mt-2">
              After updating environment variables, restart the API container:
              <code className="ml-2 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-xs">
                docker-compose restart api
              </code>
            </p>
          </div>
        </AlertDescription>
      </Alert>
    </div>
  );
}
