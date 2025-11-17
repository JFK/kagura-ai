/**
 * System Management API Client
 *
 * Issue #684 - System Backend Status and Vector Collections
 */

import { apiClient } from './api';

// ============================================================================
// Types
// ============================================================================

export interface BackendInfo {
  type: string;
  url: string | null;
  connected: boolean;
  status: 'ok' | 'warning' | 'error' | 'info';
  message: string;
  stats: Record<string, any> | null;
}

export interface BackendStatusResponse {
  database: BackendInfo;
  vector_db: BackendInfo;
  cache: BackendInfo;
}

export interface VectorCollectionInfo {
  name: string;
  vector_count: number;
  embedding_dimension: number | null;
}

export interface VectorCollectionsResponse {
  backend: string;
  collections: VectorCollectionInfo[];
}

// ============================================================================
// System APIs
// ============================================================================

/**
 * Get backend status (Database, Vector DB, Cache)
 */
export async function getBackendStatus(): Promise<BackendStatusResponse> {
  return await apiClient.get<BackendStatusResponse>('/system/backends');
}

/**
 * Get vector database collections
 */
export async function getVectorCollections(): Promise<VectorCollectionsResponse> {
  return await apiClient.get<VectorCollectionsResponse>('/system/vector/collections');
}
