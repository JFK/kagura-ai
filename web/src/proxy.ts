/**
 * Next.js Proxy
 *
 * Issue #651 - Minimal proxy for Next.js 16
 * Migrated from middleware.ts per Next.js 16 deprecation
 *
 * Note: Authentication guards are handled in (dashboard)/layout.tsx
 * This proxy only handles static file serving optimization.
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export default async function proxy(request: NextRequest) {
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
