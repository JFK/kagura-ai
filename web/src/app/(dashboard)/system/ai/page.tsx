'use client';

/**
 * AI Configuration Settings Page
 *
 * External API Keys, Embedding Model Configuration, and Model Settings
 * Issues #690, #692: Provider selection and model configuration
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import {
  Settings,
  Database,
  Key,
  Plus,
  Trash2,
  Eye,
  EyeOff,
  Upload,
  ExternalLink,
  AlertCircle,
  Loader2,
  Edit,
  RefreshCw,
} from 'lucide-react';

// API clients
import {
  listExternalAPIKeys,
  createExternalAPIKey,
  updateExternalAPIKey,
  deleteExternalAPIKey,
  importExternalAPIKeys,
  type ExternalAPIKey,
} from '@/lib/external-keys';
import { PROVIDERS, getProviderConfig, getProviderIds } from '@/lib/provider-config';
import {
  EMBEDDING_MODELS,
  getEmbeddingModels,
  getEmbeddingModel,
  type EmbeddingModel,
} from '@/lib/embedding-models';
import { apiClient } from '@/lib/api';

export default function AIConfigPage() {
  const { toast } = useToast();

  // External API Keys state
  const [externalKeys, setExternalKeys] = useState<ExternalAPIKey[]>([]);
  const [isLoadingKeys, setIsLoadingKeys] = useState(true);
  const [showAddKeyDialog, setShowAddKeyDialog] = useState(false);
  const [showEditKeyDialog, setShowEditKeyDialog] = useState(false);
  const [isImporting, setIsImporting] = useState(false);

  // Add/Edit key form state
  const [selectedProvider, setSelectedProvider] = useState('openai');
  const [selectedKeyName, setSelectedKeyName] = useState('');
  const [keyValue, setKeyValue] = useState('');
  const [showKeyValue, setShowKeyValue] = useState(false);
  const [editingKeyName, setEditingKeyName] = useState<string | null>(null);

  // Embedding configuration state
  const [embeddingProvider, setEmbeddingProvider] = useState<'openai' | 'local'>('openai');
  const [embeddingModel, setEmbeddingModel] = useState('text-embedding-3-large');
  const [currentEmbeddingProvider, setCurrentEmbeddingProvider] = useState<string>('');
  const [currentEmbeddingModel, setCurrentEmbeddingModel] = useState<string>('');
  const [isSavingEmbedding, setIsSavingEmbedding] = useState(false);

  // Model configuration state
  const [defaultModel, setDefaultModel] = useState('');
  const [codingModel, setCodingModel] = useState('');

  // Load external API keys
  useEffect(() => {
    loadExternalKeys();
  }, []);

  // Load current configuration
  useEffect(() => {
    loadCurrentConfig();
  }, []);

  const loadExternalKeys = async () => {
    try {
      setIsLoadingKeys(true);
      const keys = await listExternalAPIKeys();
      setExternalKeys(keys);
    } catch (error) {
      console.error('Failed to load external API keys:', error);
      toast({
        title: 'Error',
        description: 'Failed to load external API keys',
        variant: 'destructive',
      });
    } finally {
      setIsLoadingKeys(false);
    }
  };

  const loadCurrentConfig = async () => {
    try {
      // Load embedding configuration
      const embProviderRes = await apiClient.get<{ value: string }>('/config/EMBEDDING_PROVIDER');
      const embModelRes = await apiClient.get<{ value: string }>('/config/EMBEDDING_MODEL');

      setCurrentEmbeddingProvider(embProviderRes.value || 'openai');
      setCurrentEmbeddingModel(embModelRes.value || 'text-embedding-3-large');

      setEmbeddingProvider(embProviderRes.value === 'local' ? 'local' : 'openai');
      setEmbeddingModel(embModelRes.value || 'text-embedding-3-large');

      // Load default models
      const defaultModelRes = await apiClient.get<{ value: string }>('/config/DEFAULT_MODEL');
      const codingModelRes = await apiClient.get<{ value: string }>('/config/CODING_MODEL');

      setDefaultModel(defaultModelRes.value || 'gpt-4-turbo');
      setCodingModel(codingModelRes.value || 'claude-3-5-sonnet-20250128');
    } catch (error) {
      console.error('Failed to load configuration:', error);
    }
  };

  const handleAddKey = async () => {
    if (!selectedKeyName || !keyValue) {
      toast({
        title: 'Error',
        description: 'Please select a key name and enter a value',
        variant: 'destructive',
      });
      return;
    }

    try {
      await createExternalAPIKey({
        key_name: selectedKeyName,
        provider: selectedProvider,
        value: keyValue,
      });

      toast({
        title: 'API Key added',
        description: `${selectedKeyName} has been saved successfully`,
      });

      setShowAddKeyDialog(false);
      setSelectedProvider('openai');
      setSelectedKeyName('');
      setKeyValue('');
      setShowKeyValue(false);
      loadExternalKeys();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to add API key',
        variant: 'destructive',
      });
    }
  };

  const handleEditKey = async () => {
    if (!editingKeyName || !keyValue) {
      toast({
        title: 'Error',
        description: 'Please enter a new value',
        variant: 'destructive',
      });
      return;
    }

    try {
      await updateExternalAPIKey(editingKeyName, keyValue);

      toast({
        title: 'API Key updated',
        description: `${editingKeyName} has been updated successfully`,
      });

      setShowEditKeyDialog(false);
      setEditingKeyName(null);
      setKeyValue('');
      setShowKeyValue(false);
      loadExternalKeys();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update API key',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteKey = async (keyName: string) => {
    if (!confirm(`Are you sure you want to delete ${keyName}?`)) {
      return;
    }

    try {
      await deleteExternalAPIKey(keyName);

      toast({
        title: 'API Key deleted',
        description: `${keyName} has been removed`,
      });

      loadExternalKeys();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete API key',
        variant: 'destructive',
      });
    }
  };

  const handleImportKeys = async () => {
    try {
      setIsImporting(true);
      const result = await importExternalAPIKeys();

      const messages = [];
      if (result.created.length > 0) {
        messages.push(`Created: ${result.created.join(', ')}`);
      }
      if (result.skipped.length > 0) {
        messages.push(`Skipped (already exist): ${result.skipped.join(', ')}`);
      }
      if (result.failed.length > 0) {
        messages.push(`Failed: ${result.failed.map(([k, e]) => `${k} (${e})`).join(', ')}`);
      }

      toast({
        title: 'Import completed',
        description: messages.join('\n'),
      });

      loadExternalKeys();
    } catch (error: any) {
      toast({
        title: 'Import failed',
        description: error.message || 'Failed to import API keys',
        variant: 'destructive',
      });
    } finally {
      setIsImporting(false);
    }
  };

  const handleSaveEmbeddingConfig = async () => {
    try {
      setIsSavingEmbedding(true);

      // Save embedding provider
      await apiClient.put('/config/EMBEDDING_PROVIDER', {
        value: embeddingProvider,
      });

      // Save embedding model
      await apiClient.put('/config/EMBEDDING_MODEL', {
        value: embeddingModel,
      });

      setCurrentEmbeddingProvider(embeddingProvider);
      setCurrentEmbeddingModel(embeddingModel);

      toast({
        title: 'Configuration saved',
        description: 'Embedding configuration has been updated. Restart the API server to apply changes.',
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to save configuration',
        variant: 'destructive',
      });
    } finally {
      setIsSavingEmbedding(false);
    }
  };

  const openAddKeyDialog = () => {
    setSelectedProvider('openai');
    setSelectedKeyName('');
    setKeyValue('');
    setShowKeyValue(false);
    setShowAddKeyDialog(true);
  };

  const openEditKeyDialog = (key: ExternalAPIKey) => {
    setEditingKeyName(key.key_name);
    setKeyValue('');
    setShowKeyValue(false);
    setShowEditKeyDialog(true);
  };

  // Get available key names for selected provider
  const availableKeyNames = getProviderConfig(selectedProvider)?.keyNames || [];

  // Get available embedding models for selected provider
  const availableEmbeddingModels = getEmbeddingModels(embeddingProvider);
  const currentModelInfo = getEmbeddingModel(embeddingProvider, embeddingModel);

  // Check if embedding config has changed
  const embeddingConfigChanged =
    embeddingProvider !== currentEmbeddingProvider || embeddingModel !== currentEmbeddingModel;

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Configuration</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-2">
          Manage external API keys, embedding models, and AI model settings.
        </p>
      </div>

      {/* External API Keys */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              External API Keys
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={handleImportKeys}
                disabled={isImporting}
              >
                {isImporting ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Upload className="h-4 w-4 mr-2" />
                )}
                Import from .env.cloud
              </Button>
              <Button size="sm" onClick={openAddKeyDialog}>
                <Plus className="h-4 w-4 mr-2" />
                Add Key
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            Manage API keys for external AI providers (OpenAI, Anthropic, Google, Brave, etc.)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoadingKeys ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
              <span className="ml-2 text-sm text-slate-500">Loading API keys...</span>
            </div>
          ) : externalKeys.length === 0 ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                No API keys configured. Add one to enable external AI services.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-3">
              {externalKeys.map((key) => {
                const providerConfig = getProviderConfig(key.provider);
                return (
                  <div
                    key={key.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{key.key_name}</p>
                        <Badge variant="secondary">{providerConfig?.name || key.provider}</Badge>
                        {providerConfig?.docsUrl && (
                          <a
                            href={providerConfig.docsUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                          >
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                      <p className="text-sm text-slate-500 font-mono mt-1">{key.masked_value}</p>
                      <p className="text-xs text-slate-400 mt-1">
                        Updated: {new Date(key.updated_at).toLocaleDateString()}
                        {key.updated_by && ` by ${key.updated_by}`}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => openEditKeyDialog(key)}
                        className="text-blue-500 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-950"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteKey(key.key_name)}
                        className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Embedding Model Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Embedding Configuration
          </CardTitle>
          <CardDescription>
            Configure embedding model for semantic search and memory indexing
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {/* Provider Selection */}
            <div className="space-y-2">
              <Label htmlFor="embedding-provider">Embedding Provider</Label>
              <Select
                value={embeddingProvider}
                onValueChange={(value: 'openai' | 'local') => {
                  setEmbeddingProvider(value);
                  // Set default model for provider
                  const models = getEmbeddingModels(value);
                  if (models.length > 0) {
                    setEmbeddingModel(models[0].id);
                  }
                }}
              >
                <SelectTrigger id="embedding-provider">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">OpenAI API</SelectItem>
                  <SelectItem value="local">Local (Sentence Transformers)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-500">
                {embeddingProvider === 'openai'
                  ? 'Requires OPENAI_API_KEY'
                  : 'Runs locally, no API key required'}
              </p>
            </div>

            {/* Model Selection */}
            <div className="space-y-2">
              <Label htmlFor="embedding-model">Embedding Model</Label>
              <Select value={embeddingModel} onValueChange={setEmbeddingModel}>
                <SelectTrigger id="embedding-model">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {availableEmbeddingModels.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      {model.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {currentModelInfo && (
                <p className="text-xs text-slate-500">
                  {currentModelInfo.dimensions} dimensions
                  {currentModelInfo.cost && ` • ${currentModelInfo.cost}`}
                  {currentModelInfo.ram && ` • ${currentModelInfo.ram}`}
                </p>
              )}
            </div>
          </div>

          {embeddingConfigChanged && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Configuration has changed. Save and restart the API server to apply.
              </AlertDescription>
            </Alert>
          )}

          <div className="flex gap-2 pt-2">
            <Button
              onClick={handleSaveEmbeddingConfig}
              disabled={!embeddingConfigChanged || isSavingEmbedding}
            >
              {isSavingEmbedding ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Settings className="h-4 w-4 mr-2" />
              )}
              Save Configuration
            </Button>
            {embeddingConfigChanged && (
              <Button
                variant="outline"
                onClick={() => {
                  setEmbeddingProvider(currentEmbeddingProvider as 'openai' | 'local');
                  setEmbeddingModel(currentEmbeddingModel);
                }}
              >
                Reset
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Model Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Model Configuration
          </CardTitle>
          <CardDescription>Default models for different tasks</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="default-model">Default Chat Model</Label>
            <Input
              id="default-model"
              value={defaultModel}
              disabled
              className="bg-slate-50 dark:bg-slate-900"
            />
            <p className="text-xs text-slate-500">Used for general conversational tasks</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="coding-model">Coding Model</Label>
            <Input
              id="coding-model"
              value={codingModel}
              disabled
              className="bg-slate-50 dark:bg-slate-900"
            />
            <p className="text-xs text-slate-500">Used for code generation and analysis</p>
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Model configuration is currently read-only. Contact your administrator to change these
              settings.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* Reranker Configuration (Placeholder) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5" />
            Reranker Configuration
          </CardTitle>
          <CardDescription>Configure reranking models for improved search results</CardDescription>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Reranker configuration coming soon. This feature will allow you to configure Cohere,
              Jina, or local reranking models for enhanced search accuracy.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* Add Key Dialog */}
      <Dialog open={showAddKeyDialog} onOpenChange={setShowAddKeyDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add External API Key</DialogTitle>
            <DialogDescription>
              Add a new API key for external AI services. Keys are encrypted at rest.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="provider">Provider</Label>
              <Select value={selectedProvider} onValueChange={setSelectedProvider}>
                <SelectTrigger id="provider">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {getProviderIds().map((providerId) => (
                    <SelectItem key={providerId} value={providerId}>
                      {PROVIDERS[providerId].name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="key-name">Key Name</Label>
              <Select value={selectedKeyName} onValueChange={setSelectedKeyName}>
                <SelectTrigger id="key-name">
                  <SelectValue placeholder="Select key name" />
                </SelectTrigger>
                <SelectContent>
                  {availableKeyNames.map((keyName) => (
                    <SelectItem key={keyName} value={keyName}>
                      {keyName}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="key-value">API Key Value</Label>
              <div className="flex gap-2">
                <Input
                  id="key-value"
                  type={showKeyValue ? 'text' : 'password'}
                  value={keyValue}
                  onChange={(e) => setKeyValue(e.target.value)}
                  placeholder={getProviderConfig(selectedProvider)?.placeholder}
                  className="font-mono"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setShowKeyValue(!showKeyValue)}
                  type="button"
                >
                  {showKeyValue ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              {getProviderConfig(selectedProvider)?.docsUrl && (
                <a
                  href={getProviderConfig(selectedProvider)?.docsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-500 hover:text-blue-700 flex items-center gap-1"
                >
                  Get API key <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddKeyDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddKey}>Add Key</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Key Dialog */}
      <Dialog open={showEditKeyDialog} onOpenChange={setShowEditKeyDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update API Key</DialogTitle>
            <DialogDescription>
              Update the value for {editingKeyName}. The new value will be encrypted at rest.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-key-value">New API Key Value</Label>
              <div className="flex gap-2">
                <Input
                  id="edit-key-value"
                  type={showKeyValue ? 'text' : 'password'}
                  value={keyValue}
                  onChange={(e) => setKeyValue(e.target.value)}
                  placeholder="Enter new API key value"
                  className="font-mono"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setShowKeyValue(!showKeyValue)}
                  type="button"
                >
                  {showKeyValue ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditKeyDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleEditKey}>Update Key</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
