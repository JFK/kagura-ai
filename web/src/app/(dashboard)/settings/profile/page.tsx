'use client';

/**
 * User Profile Settings Page
 *
 * Coming Soon: User profile and preferences management
 * Issue #664: Web UI Redesign Phase 1
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Info, User } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Profile</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-2">
          Manage your user profile and preferences.
        </p>
      </div>

      {/* Coming Soon Alert */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          <div className="font-semibold mb-1">Coming Soon</div>
          <p className="text-sm">
            This page will allow you to manage your profile information, preferences, and personal
            settings. Check back in the next release!
          </p>
        </AlertDescription>
      </Alert>

      {/* Current User Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Current User
          </CardTitle>
          <CardDescription>Your currently logged-in user information</CardDescription>
        </CardHeader>
        <CardContent>
          {user && (
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Name</p>
                <p className="text-base">{user.name}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Email</p>
                <p className="text-base">{user.email}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Role</p>
                <p className="text-base capitalize">{user.role || 'user'}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Preview Card */}
      <Card>
        <CardHeader>
          <CardTitle>Planned Features</CardTitle>
          <CardDescription>Features that will be available in this section</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-blue-500" />
              Edit Profile Information
            </li>
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-blue-500" />
              Change Password
            </li>
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-blue-500" />
              Notification Preferences
            </li>
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-blue-500" />
              Theme and Display Settings
            </li>
            <li className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-blue-500" />
              Memory Preferences (for AI context)
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
