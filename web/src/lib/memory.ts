/**
 * Memory API Client
 *
 * Functions for interacting with Kagura Memory Cloud API
 */

import { apiClient } from './api';
import type {
  Memory,
  CreateMemoryRequest,
  UpdateMemoryRequest,
  MemorySearchParams,
  MemoryListResponse,
  MemoryStatsResponse,
} from './types/memory';

/**
 * Get list of memories with optional filters
 */
export async function getMemories(
  params: MemorySearchParams = {}
): Promise<MemoryListResponse> {
  const searchParams = new URLSearchParams();

  if (params.query) searchParams.append('query', params.query);
  if (params.scope) searchParams.append('scope', params.scope);
  if (params.agent_name) searchParams.append('agent_name', params.agent_name);
  if (params.tags) params.tags.forEach(tag => searchParams.append('tags', tag));
  if (params.min_importance !== undefined) searchParams.append('min_importance', params.min_importance.toString());
  if (params.max_importance !== undefined) searchParams.append('max_importance', params.max_importance.toString());
  if (params.limit) searchParams.append('limit', params.limit.toString());
  if (params.offset) searchParams.append('offset', params.offset.toString());

  const queryString = searchParams.toString();
  const endpoint = `/api/v1/memory${queryString ? `?${queryString}` : ''}`;

  return apiClient.get<MemoryListResponse>(endpoint);
}

/**
 * Get a single memory by key
 */
export async function getMemory(
  key: string,
  scope: string = 'persistent',
  agentName: string = 'global'
): Promise<Memory> {
  const searchParams = new URLSearchParams({
    scope,
    agent_name: agentName,
  });

  return apiClient.get<Memory>(`/api/v1/memory/${encodeURIComponent(key)}?${searchParams.toString()}`);
}

/**
 * Create a new memory
 */
export async function createMemory(
  userId: string,
  data: CreateMemoryRequest
): Promise<Memory> {
  return apiClient.post<Memory>('/api/v1/memory', {
    user_id: userId,
    ...data,
  });
}

/**
 * Update an existing memory
 */
export async function updateMemory(
  key: string,
  userId: string,
  data: UpdateMemoryRequest,
  scope: string = 'persistent',
  agentName: string = 'global'
): Promise<Memory> {
  return apiClient.put<Memory>(`/api/v1/memory/${encodeURIComponent(key)}`, {
    user_id: userId,
    scope,
    agent_name: agentName,
    ...data,
  });
}

/**
 * Delete a memory
 */
export async function deleteMemory(
  key: string,
  userId: string,
  scope: string = 'persistent',
  agentName: string = 'global'
): Promise<void> {
  const searchParams = new URLSearchParams({
    user_id: userId,
    scope,
    agent_name: agentName,
  });

  return apiClient.delete<void>(`/api/v1/memory/${encodeURIComponent(key)}?${searchParams.toString()}`);
}

/**
 * Get memory statistics
 */
export async function getMemoryStats(userId: string): Promise<MemoryStatsResponse> {
  return apiClient.get<MemoryStatsResponse>(`/api/v1/memory/stats?user_id=${userId}`);
}

/**
 * Search memories semantically
 */
export async function searchMemories(
  userId: string,
  query: string,
  params: Omit<MemorySearchParams, 'query'> = {}
): Promise<MemoryListResponse> {
  return getMemories({
    ...params,
    query,
  });
}
