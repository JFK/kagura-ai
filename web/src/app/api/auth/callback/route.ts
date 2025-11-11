/**
 * OAuth2 Callback Handler
 *
 * Handles the OAuth2 callback from Google, exchanges the authorization code
 * for a session token, and redirects to the dashboard.
 */

import { NextRequest, NextResponse } from 'next/server';
import { handleAuthCallback } from '@/lib/auth';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get('code');
  const state = searchParams.get('state');
  const error = searchParams.get('error');

  // Handle OAuth2 error
  if (error) {
    console.error('OAuth2 error:', error);
    return NextResponse.redirect(
      new URL(`/login?error=${encodeURIComponent('Authentication failed. Please try again.')}`, request.url)
    );
  }

  // Validate required parameters
  if (!code || !state) {
    console.error('Missing code or state parameter');
    return NextResponse.redirect(
      new URL(`/login?error=${encodeURIComponent('Invalid authentication response.')}`, request.url)
    );
  }

  try {
    // Exchange code for session token
    const authResponse = await handleAuthCallback(code, state);

    // Backend sets HTTP-only cookie via Set-Cookie header
    // The session is now established

    // Redirect to dashboard
    return NextResponse.redirect(new URL('/dashboard', request.url));
  } catch (err) {
    console.error('Authentication callback failed:', err);

    const errorMessage =
      err instanceof Error
        ? err.message
        : 'Authentication failed. Please try again.';

    return NextResponse.redirect(
      new URL(`/login?error=${encodeURIComponent(errorMessage)}`, request.url)
    );
  }
}
