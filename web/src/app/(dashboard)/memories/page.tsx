/**
 * Redirect: /memories → /memory/overview
 *
 * This page maintains backward compatibility for the old URL.
 * Will be removed in a future release.
 */

import { redirect } from 'next/navigation';

export default function MemoriesRedirect() {
  redirect('/memory/overview');
}
