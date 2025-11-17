/**
 * Redirect: /integrations/kagura-apps → /integrations/app-credentials
 *
 * This page maintains backward compatibility for the old URL.
 * Will be removed in a future release.
 */

import { redirect } from 'next/navigation';

export default function KaguraAppsRedirect() {
  redirect('/integrations/app-credentials');
}
