/**
 * Role-Based Access Control (RBAC) Utilities
 *
 * Provides role checking and permission utilities for the Web UI.
 * Issue #664: Web UI Redesign Phase 1
 */

import { User } from './auth';

/**
 * User roles in the system
 */
export enum Role {
  ADMIN = 'admin',
  USER = 'user',
  READ_ONLY = 'readonly',
}

/**
 * Role hierarchy: higher number = more permissions
 */
const ROLE_HIERARCHY: Record<Role, number> = {
  [Role.ADMIN]: 3,
  [Role.USER]: 2,
  [Role.READ_ONLY]: 1,
};

/**
 * Check if user has a specific role
 */
export function hasRole(user: User | null | undefined, role: Role): boolean {
  if (!user || !user.role) {
    return false;
  }

  const userRoleLevel = ROLE_HIERARCHY[user.role as Role] ?? 0;
  const requiredRoleLevel = ROLE_HIERARCHY[role];

  return userRoleLevel >= requiredRoleLevel;
}

/**
 * Check if user is admin
 */
export function isAdmin(user: User | null | undefined): boolean {
  return hasRole(user, Role.ADMIN);
}

/**
 * Check if user can edit/modify resources
 */
export function canEdit(user: User | null | undefined): boolean {
  return hasRole(user, Role.USER);
}

/**
 * Check if user can only read resources
 */
export function isReadOnly(user: User | null | undefined): boolean {
  if (!user || !user.role) {
    return true; // Default to read-only
  }
  return user.role === Role.READ_ONLY;
}

/**
 * Get user role label for display
 */
export function getRoleLabel(role: string | undefined): string {
  switch (role) {
    case Role.ADMIN:
      return 'Administrator';
    case Role.USER:
      return 'User';
    case Role.READ_ONLY:
      return 'Read Only';
    default:
      return 'Unknown';
  }
}

/**
 * Get role badge color (for UI display)
 */
export function getRoleBadgeColor(
  role: string | undefined
): 'default' | 'destructive' | 'secondary' | 'outline' {
  switch (role) {
    case Role.ADMIN:
      return 'destructive'; // Red for admin
    case Role.USER:
      return 'default'; // Default color
    case Role.READ_ONLY:
      return 'secondary'; // Gray for read-only
    default:
      return 'outline';
  }
}
