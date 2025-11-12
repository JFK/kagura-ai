/**
 * Authentication Utilities
 *
 * Handles OAuth2 authentication flows, user information retrieval, and session management.
 */

import { apiClient } from './api';

export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  role?: string;
}

export interface AuthResponse {
  user: User;
  token?: string;
}

/**
 * Get the OAuth2 authorization URL
 * Redirects to Google OAuth2 consent screen
 */
export async function getAuthUrl(): Promise<string> {
  try {
    const response = await apiClient.get<{ authorization_url: string }>(
      '/auth/login'
    );
    return response.authorization_url;
  } catch (error) {
    console.error('Failed to get auth URL:', error);
    throw error;
  }
}

/**
 * Handle OAuth2 callback
 * Exchange authorization code for session token
 */
export async function handleAuthCallback(
  code: string,
  state: string
): Promise<AuthResponse> {
  try {
    const response = await apiClient.get<{ user: User; token?: string }>(
      `/auth/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`
    );
    return {
      user: response.user,
      token: response.token,
    };
  } catch (error) {
    console.error('OAuth2 callback failed:', error);
    throw error;
  }
}

/**
 * Get current authenticated user information
 */
export async function getCurrentUser(): Promise<User | null> {
  try {
    const response = await apiClient.get<{ user: User }>('/auth/me');
    return response.user;
  } catch (error) {
    // If 401 Unauthorized, user is not authenticated
    if ((error as { status?: number }).status === 401) {
      return null;
    }
    console.error('Failed to get current user:', error);
    throw error;
  }
}

/**
 * Logout current user
 * Clears session on backend
 */
export async function logout(): Promise<void> {
  try {
    await apiClient.post('/auth/logout');
  } catch (error) {
    console.error('Logout failed:', error);
    throw error;
  }
}

/**
 * Check if user is authenticated
 * Returns true if session is valid
 */
export async function isAuthenticated(): Promise<boolean> {
  try {
    const user = await getCurrentUser();
    return user !== null;
  } catch {
    return false;
  }
}
