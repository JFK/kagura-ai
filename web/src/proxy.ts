/**
 * Next.js Proxy for Protected Routes
 *
 * Checks authentication status for protected routes and redirects
 * unauthenticated users to the login page.
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip middleware for public routes
  if (
    pathname === '/login' ||
    pathname === '/' ||
    pathname.startsWith('/api/auth') ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/favicon')
  ) {
    return NextResponse.next();
  }

  // Check if the route is protected (starts with /dashboard)
  if (pathname.startsWith('/dashboard')) {
    try {
      // Check authentication by calling /auth/me endpoint
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          // Forward cookies from the request
          Cookie: request.headers.get('cookie') || '',
        },
        credentials: 'include',
      });

      // If not authenticated (401), redirect to login
      if (response.status === 401) {
        const loginUrl = new URL('/login', request.url);
        return NextResponse.redirect(loginUrl);
      }

      // If authenticated, allow access
      if (response.ok) {
        return NextResponse.next();
      }

      // For other errors, redirect to login
      console.error('Authentication check failed:', response.status);
      const loginUrl = new URL('/login', request.url);
      return NextResponse.redirect(loginUrl);
    } catch (error) {
      console.error('Middleware authentication check failed:', error);
      // On error, redirect to login for safety
      const loginUrl = new URL('/login', request.url);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
