/**
 * Logout Handler
 *
 * Clears the user session on the backend and redirects to the home page.
 */

import { NextResponse } from 'next/server';
import { logout } from '@/lib/auth';

export async function POST() {
  try {
    // Clear session on backend
    await logout();

    // Redirect to home page
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Logout failed:', error);
    return NextResponse.json(
      { error: 'Logout failed' },
      { status: 500 }
    );
  }
}

export async function GET() {
  // Support GET requests for convenience (e.g., direct navigation)
  try {
    await logout();
    return NextResponse.redirect(new URL('/', process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'));
  } catch (error) {
    console.error('Logout failed:', error);
    return NextResponse.redirect(new URL('/', process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'));
  }
}
