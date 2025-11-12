/**
 * Next.js Middleware
 *
 * Issue #651 - Minimal middleware for Next.js
 *
 * Note: Authentication guards are handled in (dashboard)/layout.tsx
 * This middleware only handles static file serving optimization.
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export default async function middleware(request: NextRequest) {
  // All requests pass through (no special handling needed)
  // Authentication is handled in (dashboard)/layout.tsx
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
