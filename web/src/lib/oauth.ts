/**
 * OAuth2 Client and Provider Management API Client
 *
 * Issue #684 - OAuth2 Settings UI
 */

import { apiClient } from './api';

// ============================================================================
// Types
// ============================================================================

export interface OAuth2Provider {
  name: string;
  display_name: string;
  client_id: string | null;
  authorization_url: string;
  token_url: string;
  scopes: string[];
  enabled: boolean;
  configured: boolean;
}

export interface OAuth2Client {
  id: number;
  client_id: string;
  client_name: string;
  redirect_uris: string[];
  grant_types: string[];
  response_types: string[];
  scope: string;
  token_endpoint_auth_method: string;
  created_at: string;
}

export interface OAuth2ClientWithSecret extends OAuth2Client {
  client_secret: string;
}

export interface OAuth2ClientCreateRequest {
  client_name: string;
  redirect_uris: string[];
  grant_types?: string[];
  response_types?: string[];
  scope?: string;
  token_endpoint_auth_method?: string;
}

export interface OAuth2ClientUpdateRequest {
  client_name?: string;
  redirect_uris?: string[];
  scope?: string;
}

// ============================================================================
// OAuth2 Provider Management
// ============================================================================

/**
 * List configured OAuth2 providers
 */
export async function getOAuth2Providers(): Promise<OAuth2Provider[]> {
  return await apiClient.get<OAuth2Provider[]>('/auth/oauth2/providers');
}

// ============================================================================
// OAuth2 Client Management
// ============================================================================

/**
 * List all registered OAuth2 clients
 */
export async function getOAuth2Clients(): Promise<OAuth2Client[]> {
  return await apiClient.get<OAuth2Client[]>('/auth/oauth2/clients');
}

/**
 * Create a new OAuth2 client
 */
export async function createOAuth2Client(
  data: OAuth2ClientCreateRequest
): Promise<OAuth2ClientWithSecret> {
  return await apiClient.post<OAuth2ClientWithSecret>(
    '/auth/oauth2/clients',
    data
  );
}

/**
 * Get OAuth2 client details
 */
export async function getOAuth2Client(clientId: string): Promise<OAuth2Client> {
  return await apiClient.get<OAuth2Client>(`/auth/oauth2/clients/${clientId}`);
}

/**
 * Update OAuth2 client
 */
export async function updateOAuth2Client(
  clientId: string,
  data: OAuth2ClientUpdateRequest
): Promise<OAuth2Client> {
  return await apiClient.put<OAuth2Client>(
    `/auth/oauth2/clients/${clientId}`,
    data
  );
}

/**
 * Delete OAuth2 client
 */
export async function deleteOAuth2Client(clientId: string): Promise<void> {
  await apiClient.delete(`/auth/oauth2/clients/${clientId}`);
}
