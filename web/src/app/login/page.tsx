'use client';

/**
 * Login Page - Premium Redesign
 *
 * Matches landing page design:
 * - MkDocs brand colors (Green #059669)
 * - Glassmorphism effects
 * - Gradient backgrounds
 * - Professional Supabase/Vercel style
 */

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getAuthUrl } from '@/lib/auth';
import { ArrowRight, AlertCircle, Sparkles, Shield, Zap } from 'lucide-react';

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const errorParam = searchParams.get('error');
    if (errorParam) {
      setError(decodeURIComponent(errorParam));
    }
  }, [searchParams]);

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const authUrl = await getAuthUrl();
      window.location.href = authUrl;
    } catch (err) {
      setIsLoading(false);
      setError(err instanceof Error ? err.message : 'Failed to initiate login');
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-white">
      {/* Background Pattern */}
      <div className="absolute inset-0 -z-10 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px]" />
      <div className="absolute inset-0 -z-10 bg-gradient-to-b from-white via-gray-50/50 to-white" />

      {/* Gradient Orbs */}
      <div className="pointer-events-none absolute -left-1/4 -top-1/4 h-96 w-96 rounded-full bg-brand-green-300/30 blur-3xl" />
      <div className="pointer-events-none absolute -right-1/4 -bottom-1/4 h-96 w-96 rounded-full bg-emerald-300/30 blur-3xl" />

      <div className="relative w-full max-w-md px-4">
        {/* Logo */}
        <div className="mb-8 flex justify-center">
          <img
            src="/kagura-logo.svg"
            alt="Kagura AI"
            className="h-24 w-auto"
          />
        </div>

        {/* Login Card with Glassmorphism */}
        <Card className="overflow-hidden border-gray-200 bg-white/80 shadow-2xl backdrop-blur-xl">
          <CardContent className="p-8">
            {/* Badge */}
            <div className="mb-6 flex justify-center">
              <div className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand-green-100 to-emerald-100 px-4 py-1.5 text-sm font-semibold text-brand-green-700">
                <Sparkles className="h-4 w-4" />
                <span>Welcome to Kagura AI</span>
              </div>
            </div>

            {/* Title */}
            <div className="mb-8 text-center">
              <h1 className="mb-2 text-3xl font-bold text-gray-900">
                Sign in to your account
              </h1>
              <p className="text-gray-600">
                Access your universal AI memory platform
              </p>
            </div>

            {/* Error Alert */}
            {error && (
              <Alert variant="destructive" className="mb-6 border-red-200 bg-red-50">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Google Sign-in Button */}
            <Button
              onClick={handleGoogleLogin}
              disabled={isLoading}
              size="lg"
              className="group relative h-14 w-full overflow-hidden bg-gradient-to-r from-brand-green-600 to-emerald-600 text-base font-semibold text-white shadow-xl shadow-brand-green-500/30 transition-all hover:scale-[1.02] hover:from-brand-green-700 hover:to-emerald-700 hover:shadow-2xl"
            >
              <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-brand-green-700 to-emerald-700 opacity-0 transition-opacity group-hover:opacity-100" />

              {isLoading ? (
                <span className="relative z-10 flex items-center justify-center gap-2">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Redirecting to Google...
                </span>
              ) : (
                <span className="relative z-10 flex items-center justify-center gap-2">
                  <svg className="h-5 w-5" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                  </svg>
                  Continue with Google
                  <ArrowRight className="ml-1 h-5 w-5 transition-transform group-hover:translate-x-1" />
                </span>
              )}
            </Button>

            {/* Features */}
            <div className="mt-8 space-y-3">
              {[
                { icon: Shield, text: 'Secure OAuth2 authentication' },
                { icon: Zap, text: 'Instant access to your memories' },
                { icon: Sparkles, text: 'Free forever, no credit card' },
              ].map((feature) => {
                const Icon = feature.icon;
                return (
                  <div key={feature.text} className="flex items-center gap-3 text-sm text-gray-700">
                    <div className="flex-shrink-0 rounded-lg bg-brand-green-100 p-2 text-brand-green-600">
                      <Icon className="h-4 w-4" />
                    </div>
                    <span>{feature.text}</span>
                  </div>
                );
              })}
            </div>

            {/* Terms */}
            <p className="mt-8 text-center text-xs text-gray-500">
              By signing in, you agree to our{' '}
              <a href="#" className="font-medium text-brand-green-600 hover:underline">
                Terms of Service
              </a>{' '}
              and{' '}
              <a href="#" className="font-medium text-brand-green-600 hover:underline">
                Privacy Policy
              </a>
            </p>
          </CardContent>
        </Card>

        {/* Back to Home */}
        <div className="mt-6 text-center">
          <button
            onClick={() => router.push('/')}
            className="text-sm font-medium text-gray-600 transition-colors hover:text-brand-green-600"
          >
            ← Back to home
          </button>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-white">
          <div className="relative">
            <div className="h-16 w-16 animate-spin rounded-full border-4 border-brand-green-200 border-t-brand-green-600" />
            <div className="absolute inset-0 h-16 w-16 animate-ping rounded-full border-4 border-brand-green-600 opacity-20" />
          </div>
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
