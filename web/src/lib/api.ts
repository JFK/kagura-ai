/**
 * API Client Utility
 *
 * Provides a centralized fetch wrapper for communicating with the Kagura Memory Cloud backend API.
 * Handles authentication, error handling, and response parsing.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ApiError {
  message: string;
  status: number;
  details?: unknown;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Generic fetch wrapper with error handling
   */
  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const defaultHeaders: HeadersInit = {
      'Content-Type': 'application/json',
    };

    // Merge headers
    const headers = {
      ...defaultHeaders,
      ...(options.headers || {}),
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        credentials: 'include', // Include cookies for session management
      });

      // Handle non-OK responses
      if (!response.ok) {
        const errorBody = await response.text();
        let errorDetails;
        try {
          errorDetails = JSON.parse(errorBody);
        } catch {
          errorDetails = { message: errorBody };
        }

        throw {
          message: errorDetails.message || `HTTP ${response.status}: ${response.statusText}`,
          status: response.status,
          details: errorDetails,
        } as ApiError;
      }

      // Handle empty responses (e.g., 204 No Content)
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        return {} as T;
      }

      return (await response.json()) as T;
    } catch (error) {
      // Re-throw ApiError
      if ((error as ApiError).status) {
        throw error;
      }

      // Wrap network errors
      throw {
        message: error instanceof Error ? error.message : 'Network error',
        status: 0,
        details: error,
      } as ApiError;
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    return this.fetch<T>(endpoint, {
      ...options,
      method: 'GET',
    });
  }

  /**
   * POST request
   */
  async post<T>(
    endpoint: string,
    body?: unknown,
    options: RequestInit = {}
  ): Promise<T> {
    return this.fetch<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * PUT request
   */
  async put<T>(
    endpoint: string,
    body?: unknown,
    options: RequestInit = {}
  ): Promise<T> {
    return this.fetch<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    return this.fetch<T>(endpoint, {
      ...options,
      method: 'DELETE',
    });
  }
}

// Singleton instance
export const apiClient = new ApiClient();
