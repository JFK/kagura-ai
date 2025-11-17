'use client';

/**
 * Configuration Settings Page
 *
 * External service configuration, API keys, and backend settings
 * Issue #672: UI Polish & Design Enhancement - Phase 2
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import {
  Settings,
  Database,
  Key,
  Server,
  Plus,
  Trash2,
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
} from 'lucide-react';

interface ApiKey {
  id: string;
  name: string;
  provider: string;
  masked_key: string;
  created_at: string;
}

interface BackendConfig {
  postgresql_url: string;
  redis_url: string;
  qdrant_url: string;
  api_url: string;
}

export default function ConfigPage() {
  const { toast } = useToast();
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [backendConfig, setBackendConfig] = useState<BackendConfig | null>(null);

  // Add API Key form state
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyProvider, setNewKeyProvider] = useState('');
  const [newKeyValue, setNewKeyValue] = useState('');
  const [showNewKey, setShowNewKey] = useState(false);

  // Load backend configuration
  useEffect(() => {
    loadBackendConfig();
    loadApiKeys();
  }, []);

  const loadBackendConfig = async () => {
    try {
      // TODO: Replace with actual API call
      // Mock data for now
      setBackendConfig({
        postgresql_url: 'postgresql://kagura:***@localhost:5432/kagura',
        redis_url: 'redis://localhost:6379/0',
        qdrant_url: 'http://localhost:6333',
        api_url: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      });
    } catch (error) {
      console.error('Failed to load backend config:', error);
    }
  };

  const loadApiKeys = async () => {
    try {
      // TODO: Replace with actual API call
      // Mock data for now
      setApiKeys([
        {
          id: '1',
          name: 'OpenAI Production',
          provider: 'OpenAI',
          masked_key: 'sk-...abc123',
          created_at: '2025-01-15',
        },
        {
          id: '2',
          name: 'Anthropic Claude',
          provider: 'Anthropic',
          masked_key: 'sk-ant-...xyz789',
          created_at: '2025-01-20',
        },
      ]);
    } catch (error) {
      console.error('Failed to load API keys:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddApiKey = () => {
    if (!newKeyName || !newKeyProvider || !newKeyValue) {
      toast({
        title: 'Error',
        description: 'Please fill in all fields',
        variant: 'destructive',
      });
      return;
    }

    // TODO: Implement API call to add key
    const newKey: ApiKey = {
      id: Date.now().toString(),
      name: newKeyName,
      provider: newKeyProvider,
      masked_key: `${newKeyValue.slice(0, 6)}...${newKeyValue.slice(-6)}`,
      created_at: new Date().toISOString().split('T')[0],
    };

    setApiKeys([...apiKeys, newKey]);
    setShowAddForm(false);
    setNewKeyName('');
    setNewKeyProvider('');
    setNewKeyValue('');
    setShowNewKey(false);

    toast({
      title: 'API Key added',
      description: 'Your API key has been saved successfully.',
    });
  };

  const handleDeleteApiKey = (id: string) => {
    // TODO: Implement API call to delete key
    setApiKeys(apiKeys.filter((key) => key.id !== id));

    toast({
      title: 'API Key deleted',
      description: 'The API key has been removed.',
    });
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Configuration</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-2">
          Manage external service configurations, API keys, and backend settings.
        </p>
      </div>

      {/* Backend Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            Backend Services
          </CardTitle>
          <CardDescription>Current backend service endpoints (read-only)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {backendConfig ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="postgresql">PostgreSQL Database</Label>
                <div className="flex items-center gap-2">
                  <Input
                    id="postgresql"
                    value={backendConfig.postgresql_url}
                    disabled
                    className="bg-slate-50 dark:bg-slate-900 font-mono text-sm"
                  />
                  <Badge variant="outline" className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    Connected
                  </Badge>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="redis">Redis Cache</Label>
                <div className="flex items-center gap-2">
                  <Input
                    id="redis"
                    value={backendConfig.redis_url}
                    disabled
                    className="bg-slate-50 dark:bg-slate-900 font-mono text-sm"
                  />
                  <Badge variant="outline" className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    Connected
                  </Badge>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="qdrant">Qdrant Vector Database</Label>
                <div className="flex items-center gap-2">
                  <Input
                    id="qdrant"
                    value={backendConfig.qdrant_url}
                    disabled
                    className="bg-slate-50 dark:bg-slate-900 font-mono text-sm"
                  />
                  <Badge variant="outline" className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    Connected
                  </Badge>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="api">API Base URL</Label>
                <Input
                  id="api"
                  value={backendConfig.api_url}
                  disabled
                  className="bg-slate-50 dark:bg-slate-900 font-mono text-sm"
                />
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-500">Loading backend configuration...</p>
          )}
        </CardContent>
      </Card>

      {/* External API Keys */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              External API Keys
            </div>
            {!showAddForm && (
              <Button size="sm" onClick={() => setShowAddForm(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Key
              </Button>
            )}
          </CardTitle>
          <CardDescription>
            Manage API keys for external AI providers (OpenAI, Anthropic, Brave, etc.)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {showAddForm && (
            <Card className="border-2 border-blue-200 dark:border-blue-800">
              <CardHeader>
                <CardTitle className="text-base">Add New API Key</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="key-name">Key Name</Label>
                  <Input
                    id="key-name"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="e.g., OpenAI Production"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="key-provider">Provider</Label>
                  <Input
                    id="key-provider"
                    value={newKeyProvider}
                    onChange={(e) => setNewKeyProvider(e.target.value)}
                    placeholder="e.g., OpenAI, Anthropic, Brave"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="key-value">API Key</Label>
                  <div className="flex gap-2">
                    <Input
                      id="key-value"
                      type={showNewKey ? 'text' : 'password'}
                      value={newKeyValue}
                      onChange={(e) => setNewKeyValue(e.target.value)}
                      placeholder="Enter your API key"
                      className="font-mono"
                    />
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setShowNewKey(!showNewKey)}
                    >
                      {showNewKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  <Button onClick={handleAddApiKey}>Add API Key</Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowAddForm(false);
                      setNewKeyName('');
                      setNewKeyProvider('');
                      setNewKeyValue('');
                      setShowNewKey(false);
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {isLoading ? (
            <p className="text-sm text-slate-500">Loading API keys...</p>
          ) : apiKeys.length === 0 ? (
            <p className="text-sm text-slate-500">
              No API keys configured. Add one to get started.
            </p>
          ) : (
            <div className="space-y-3">
              {apiKeys.map((key) => (
                <div
                  key={key.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50 dark:hover:bg-slate-900"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{key.name}</p>
                      <Badge variant="secondary">{key.provider}</Badge>
                    </div>
                    <p className="text-sm text-slate-500 font-mono mt-1">{key.masked_key}</p>
                    <p className="text-xs text-slate-400 mt-1">Added: {key.created_at}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDeleteApiKey(key.id)}
                    className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Model Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Model Configuration
          </CardTitle>
          <CardDescription>Configure default models for different tasks</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="default-model">Default Chat Model</Label>
            <Input
              id="default-model"
              value="gpt-4-turbo"
              disabled
              className="bg-slate-50 dark:bg-slate-900"
            />
            <p className="text-xs text-slate-500">
              Used for general conversational tasks
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="embedding-model">Embedding Model</Label>
            <Input
              id="embedding-model"
              value="text-embedding-3-large"
              disabled
              className="bg-slate-50 dark:bg-slate-900"
            />
            <p className="text-xs text-slate-500">
              Used for semantic search and memory indexing
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="coding-model">Coding Model</Label>
            <Input
              id="coding-model"
              value="claude-3-5-sonnet-20250128"
              disabled
              className="bg-slate-50 dark:bg-slate-900"
            />
            <p className="text-xs text-slate-500">
              Used for code generation and analysis
            </p>
          </div>

          <Button variant="outline" disabled>
            <Settings className="h-4 w-4 mr-2" />
            Configure Models (Coming Soon)
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
