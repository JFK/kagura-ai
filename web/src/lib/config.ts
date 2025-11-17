/**
 * Configuration API Client
 *
 * Provides functions for managing .env.cloud configuration through the API.
 * Supports reading, updating, and validating configuration values.
 */

import { apiClient } from './api';

/**
 * Configuration response from API
 */
export interface ConfigResponse {
  config: Record<string, string>;
  masked_keys: string[];
}

/**
 * Validation result for configuration
 */
export interface ValidationResult {
  valid: boolean;
  errors: Record<string, string>;
}

/**
 * Category configuration response
 */
export interface ConfigCategory {
  category: string;
  values: Record<string, string>;
}

/**
 * Get all configuration values
 * @param maskSensitive - Whether to mask sensitive values (default: true)
 * @returns Configuration key-value pairs
 */
export async function getConfig(maskSensitive = true): Promise<ConfigResponse> {
  const params = new URLSearchParams();
  params.append('mask_sensitive', maskSensitive.toString());

  return apiClient.get<ConfigResponse>(`/api/v1/config?${params.toString()}`);
}

/**
 * Get configuration organized by categories
 * @returns Configuration grouped by categories
 */
export async function getConfigByCategory(): Promise<ConfigCategory[]> {
  return apiClient.get<ConfigCategory[]>('/api/v1/config/categories');
}

/**
 * Update a single configuration value
 * @param key - Configuration key
 * @param value - New value
 */
export async function updateConfigValue(key: string, value: string): Promise<void> {
  await apiClient.put(`/api/v1/config/${key}`, { value });
}

/**
 * Batch update multiple configuration values
 * @param updates - Key-value pairs to update
 */
export async function batchUpdateConfig(updates: Record<string, string>): Promise<void> {
  await apiClient.post('/api/v1/config/batch', { updates });
}

/**
 * Validate configuration before saving
 * @param config - Configuration to validate
 * @returns Validation result with errors if any
 */
export async function validateConfig(config: Record<string, string>): Promise<ValidationResult> {
  return apiClient.post<ValidationResult>('/api/v1/config/validate', { config });
}
