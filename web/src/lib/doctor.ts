/**
 * Doctor API Client
 *
 * Provides methods for fetching system health check information.
 * Issue #664: Web UI Redesign Phase 1
 */

import { apiClient } from './api';

// Type definitions matching Backend Pydantic models

export interface SystemCheck {
  status: 'ok' | 'warning' | 'error';
  message: string;
}

export interface DependencyCheck {
  name: string;
  status: 'ok' | 'warning' | 'error';
  message: string;
}

export interface APICheck {
  provider: string;
  status: 'ok' | 'warning' | 'error';
  message: string;
}

export interface MCPIntegration {
  status: 'ok' | 'warning' | 'error';
  message: string;
}

export interface SystemDoctorResponse {
  python_version: SystemCheck;
  disk_space: SystemCheck;
  dependencies: DependencyCheck[];
  api_configuration: APICheck[];
  mcp_integration: MCPIntegration;
  overall_status: 'ok' | 'warning' | 'error';
  recommendations: string[];
}

export interface MemoryStats {
  database_exists: boolean;
  database_size_mb: number | null;
  persistent_count: number;
  rag_enabled: boolean;
  rag_count: number;
  reranking_enabled: boolean;
  reranking_model_installed: boolean;
}

export interface MemoryDoctorResponse {
  stats: MemoryStats;
  status: 'ok' | 'warning' | 'error' | 'info';
  recommendations: string[];
}

export interface CodingStats {
  sessions_count: number;
  projects_count: number;
}

export interface CodingDoctorResponse {
  stats: CodingStats;
  status: 'ok' | 'info';
}

/**
 * Get system health check
 */
export async function getSystemDoctor(): Promise<SystemDoctorResponse> {
  return apiClient.get<SystemDoctorResponse>('/api/v1/system/doctor');
}

/**
 * Get memory system health check
 */
export async function getMemoryDoctor(): Promise<MemoryDoctorResponse> {
  return apiClient.get<MemoryDoctorResponse>('/api/v1/memory/doctor');
}

/**
 * Get coding memory health check
 */
export async function getCodingDoctor(): Promise<CodingDoctorResponse> {
  return apiClient.get<CodingDoctorResponse>('/api/v1/coding/doctor');
}

/**
 * Get all doctor health checks
 */
export async function getAllDoctorChecks(): Promise<{
  system: SystemDoctorResponse;
  memory: MemoryDoctorResponse;
  coding: CodingDoctorResponse;
}> {
  const [system, memory, coding] = await Promise.all([
    getSystemDoctor(),
    getMemoryDoctor(),
    getCodingDoctor(),
  ]);

  return { system, memory, coding };
}
