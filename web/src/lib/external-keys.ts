import { apiClient } from './api';

export interface ExternalAPIKey {
  id: number;
  key_name: string;
  provider: string;
  masked_value: string;
  created_at: string;
  updated_at: string;
  updated_by: string | null;
}

export interface CreateExternalAPIKeyRequest {
  key_name: string;
  provider: string;
  value: string;
}

export interface UpdateExternalAPIKeyRequest {
  value: string;
}

export interface ImportResult {
  created: string[];
  skipped: string[];
  failed: [string, string][];
}

/**
 * List all external API keys, optionally filtered by provider
 */
export async function listExternalAPIKeys(provider?: string): Promise<ExternalAPIKey[]> {
  const params = provider ? `?provider=${provider}` : '';
  return apiClient.get<ExternalAPIKey[]>(`/external-api-keys${params}`);
}

/**
 * Create a new external API key
 */
export async function createExternalAPIKey(data: CreateExternalAPIKeyRequest): Promise<ExternalAPIKey> {
  return apiClient.post<ExternalAPIKey>('/external-api-keys', data);
}

/**
 * Update an existing external API key
 */
export async function updateExternalAPIKey(keyName: string, value: string): Promise<ExternalAPIKey> {
  return apiClient.put<ExternalAPIKey>(`/external-api-keys/${keyName}`, { value });
}

/**
 * Delete an external API key
 */
export async function deleteExternalAPIKey(keyName: string): Promise<void> {
  await apiClient.delete(`/external-api-keys/${keyName}`);
}

/**
 * Import API keys from .env.cloud file
 */
export async function importExternalAPIKeys(): Promise<ImportResult> {
  return apiClient.post<ImportResult>('/external-api-keys/import', {});
}
