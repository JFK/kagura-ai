'use client';

/**
 * Kagura AI Landing Page - Modern Premium Design
 * 
 * Features:
 * - Animated gradient backgrounds
 * - Glassmorphism effects
 * - Micro-interactions and hover states
 * - 3D card effects
 * - Scroll animations
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import {
  ArrowRight,
  Check,
  Terminal,
  MessageSquare,
  GitBranch,
  Brain,
  Globe,
  Zap,
  Shield,
  Code2,
  Activity,
  Database,
  Clock,
  Workflow,
  Github,
  Sparkles,
  Star,
  TrendingUp,
  Users,
  Layers,
} from 'lucide-react';

export default function LandingPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!isLoading && user) {
      router.push('/dashboard');
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-50">
        <div className="relative">
          <div className="h-16 w-16 animate-spin rounded-full border-4 border-gray-200 border-t-brand-green-600" />
          <div className="absolute inset-0 h-16 w-16 animate-ping rounded-full border-4 border-brand-green-600 opacity-20" />
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="relative min-h-screen overflow-hidden bg-white">
        {/* Animated Background Gradient Orbs */}
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div className="absolute -left-1/4 -top-1/4 h-[800px] w-[800px] animate-blob rounded-full bg-brand-green-300/30 mix-blend-multiply blur-3xl filter" />
          <div className="animation-delay-2000 absolute -right-1/4 -top-1/4 h-[800px] w-[800px] animate-blob rounded-full bg-emerald-300/30 mix-blend-multiply blur-3xl filter" />
          <div className="animation-delay-4000 absolute -bottom-1/4 left-1/2 h-[800px] w-[800px] animate-blob rounded-full bg-brand-green-400/20 mix-blend-multiply blur-3xl filter" />
        </div>

        {/* Navigation with Glassmorphism */}
        <nav className="sticky top-0 z-50 border-b border-white/20 bg-white/70 backdrop-blur-xl">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <img src="/kagura-logo.svg" alt="Kagura AI" className="h-10 w-auto" />
                  <div className="absolute -right-1 -top-1 flex h-3 w-3">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-green-400 opacity-75" />
                    <span className="relative inline-flex h-3 w-3 rounded-full bg-brand-green-500" />
                  </div>
                </div>
              </div>
              
              <div className="hidden gap-8 md:flex">
                <a href="#features" className="group relative text-sm font-medium text-gray-700 transition-colors hover:text-brand-green-600">
                  Features
                  <span className="absolute -bottom-1 left-0 h-0.5 w-0 bg-brand-green-600 transition-all group-hover:w-full" />
                </a>
                <a href="#demo" className="group relative text-sm font-medium text-gray-700 transition-colors hover:text-brand-green-600">
                  Demo
                  <span className="absolute -bottom-1 left-0 h-0.5 w-0 bg-brand-green-600 transition-all group-hover:w-full" />
                </a>
                <a href="https://docs.kagura-ai.com" className="group relative text-sm font-medium text-gray-700 transition-colors hover:text-brand-green-600">
                  Docs
                  <span className="absolute -bottom-1 left-0 h-0.5 w-0 bg-brand-green-600 transition-all group-hover:w-full" />
                </a>
                <a href="https://github.com/JFK/kagura-ai" className="group relative text-sm font-medium text-gray-700 transition-colors hover:text-brand-green-600">
                  GitHub
                  <span className="absolute -bottom-1 left-0 h-0.5 w-0 bg-brand-green-600 transition-all group-hover:w-full" />
                </a>
              </div>
              
              <div className="flex items-center gap-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push('/login')}
                  className="relative overflow-hidden transition-all hover:scale-105"
                >
                  Sign in
                </Button>
                <Button
                  size="sm"
                  onClick={() => router.push('/login')}
                  className="group relative overflow-hidden bg-gradient-to-r from-brand-green-600 to-emerald-600 transition-all hover:scale-105 hover:shadow-lg hover:shadow-brand-green-500/50"
                >
                  <span className="relative z-10">Get Started</span>
                  <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-brand-green-700 to-emerald-700 opacity-0 transition-opacity group-hover:opacity-100" />
                </Button>
              </div>
            </div>
          </div>
        </nav>

        {/* Hero Section with 3D Effects */}
        <section className={`relative px-4 py-24 sm:px-6 sm:py-32 lg:px-8 ${mounted ? 'animate-fade-in' : 'opacity-0'}`}>
          <div className="mx-auto max-w-4xl text-center">
            {/* Floating Badge */}
            <div className="mb-8 inline-flex animate-float items-center gap-2 rounded-full border border-brand-green-200 bg-gradient-to-r from-brand-green-50 to-emerald-50 px-5 py-2 shadow-lg shadow-brand-green-500/20 backdrop-blur-sm transition-all hover:scale-105 hover:shadow-xl hover:shadow-brand-green-500/30">
              <Sparkles className="h-4 w-4 text-brand-green-600" />
              <span className="bg-gradient-to-r from-brand-green-600 to-emerald-600 bg-clip-text text-sm font-semibold text-transparent">
                v4.4.0 - Now with MCP Protocol Support
              </span>
              <TrendingUp className="h-4 w-4 text-brand-green-600" />
            </div>

            {/* Main Headline with Gradient Animation */}
            <h1 className="mb-6 text-5xl font-bold leading-tight tracking-tight text-gray-900 sm:text-7xl sm:leading-tight">
              Never lose your AI context{' '}
              <span className="relative inline-block">
                <span className="animate-gradient bg-gradient-to-r from-brand-green-600 via-emerald-600 to-brand-green-600 bg-[length:200%_auto] bg-clip-text text-transparent">
                  again
                </span>
                <svg className="absolute -bottom-2 left-0 w-full" height="8" viewBox="0 0 200 8" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M0 4C0 4 50 0 100 4C150 8 200 4 200 4" stroke="url(#gradient)" strokeWidth="3" strokeLinecap="round" className="animate-draw"/>
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#059669"/>
                      <stop offset="100%" stopColor="#10b981"/>
                    </linearGradient>
                  </defs>
                </svg>
              </span>
            </h1>

            <p className="mb-4 text-xl font-semibold text-gray-800 sm:text-2xl">
              Universal AI Memory for Every Platform
            </p>

            <p className="mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-gray-600">
              Store, retrieve, and share context seamlessly across Claude, ChatGPT, Gemini, and any AI platform. Your knowledge, always accessible.
            </p>

            {/* CTA Buttons with Enhanced Effects */}
            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Button
                size="lg"
                onClick={() => router.push('/login')}
                className="group relative h-14 overflow-hidden bg-gradient-to-r from-brand-green-600 to-emerald-600 px-8 text-base font-semibold text-white shadow-2xl shadow-brand-green-500/50 transition-all hover:scale-105 hover:shadow-3xl hover:shadow-brand-green-500/60"
              >
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-brand-green-700 to-emerald-700 opacity-0 transition-opacity group-hover:opacity-100" />
                <span className="relative z-10 flex items-center">
                  <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                  </svg>
                  Start Free with Google
                  <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
                </span>
              </Button>
              
              <Button
                size="lg"
                variant="outline"
                onClick={() => window.open('https://github.com/JFK/kagura-ai', '_blank')}
                className="group h-14 border-2 border-gray-300 bg-white/50 px-8 text-base font-semibold backdrop-blur-sm transition-all hover:scale-105 hover:border-gray-400 hover:bg-white hover:shadow-xl"
              >
                <Github className="mr-2 h-5 w-5 transition-transform group-hover:rotate-12" />
                View on GitHub
                <div className="ml-3 flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs">
                  <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                  <span className="font-semibold">2.3k</span>
                </div>
              </Button>
            </div>

            {/* Trust Indicators with Icons */}
            <div className="mt-10 flex flex-wrap items-center justify-center gap-x-8 gap-y-3">
              {[
                { icon: Check, text: 'No credit card required', color: 'text-brand-green-600' },
                { icon: Zap, text: 'Free forever', color: 'text-yellow-600' },
                { icon: Shield, text: 'Open source', color: 'text-blue-600' },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.text} className="flex items-center gap-2 text-sm font-medium text-gray-700">
                    <div className={`rounded-full bg-opacity-10 p-1 ${item.color}`}>
                      <Icon className={`h-4 w-4 ${item.color}`} />
                    </div>
                    <span>{item.text}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Platform Logos with Glassmorphism Cards */}
        <section className="border-y border-gray-200/50 bg-gradient-to-b from-gray-50/50 to-white py-16">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mb-10 flex items-center justify-center gap-3">
              <Users className="h-5 w-5 text-gray-400" />
              <p className="text-center text-sm font-semibold uppercase tracking-wider text-gray-500">
                Works seamlessly with all major AI platforms
              </p>
            </div>
            
            <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
              {[
                { name: 'Claude', icon: '🤖', gradient: 'from-purple-500 to-pink-500' },
                { name: 'ChatGPT', icon: '💬', gradient: 'from-green-500 to-emerald-500' },
                { name: 'Gemini', icon: '✨', gradient: 'from-blue-500 to-cyan-500' },
                { name: 'MCP Protocol', icon: '🔌', gradient: 'from-orange-500 to-red-500' },
              ].map((platform, index) => (
                <div
                  key={platform.name}
                  className="group relative overflow-hidden rounded-2xl border border-gray-200 bg-white/80 p-8 backdrop-blur-sm transition-all hover:scale-105 hover:border-transparent hover:shadow-2xl"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${platform.gradient} opacity-0 transition-opacity group-hover:opacity-10`} />
                  <div className="relative flex flex-col items-center justify-center">
                    <span className="mb-3 text-4xl transition-transform group-hover:scale-110">{platform.icon}</span>
                    <span className="text-sm font-semibold text-gray-700">{platform.name}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Demo Section with 3D Cards */}
        <section id="demo" className="px-4 py-24 sm:px-6 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="mb-16 text-center">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-brand-green-100 px-4 py-1.5 text-sm font-semibold text-brand-green-700">
                <Layers className="h-4 w-4" />
                <span>Live Demo</span>
              </div>
              <h2 className="mb-4 text-4xl font-bold text-gray-900 sm:text-5xl">See it in action</h2>
              <p className="text-xl text-gray-600">Three powerful use cases that transform your AI workflow</p>
            </div>

            <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
              {[
                {
                  icon: Terminal,
                  title: 'Coding Sessions',
                  description: 'Track every decision, error, and solution across your development workflow',
                  command: 'kagura coding start --project my-app',
                  features: ['Files tracked', 'Errors resolved', 'Context preserved'],
                  gradient: 'from-blue-500 to-cyan-500',
                },
                {
                  icon: MessageSquare,
                  title: 'AI Conversations',
                  description: 'Preserve context across Claude, ChatGPT, and Gemini sessions',
                  command: 'kagura memory store --tags ai,architecture',
                  features: ['Cross-platform', 'Permanent storage', 'Semantic search'],
                  gradient: 'from-purple-500 to-pink-500',
                },
                {
                  icon: GitBranch,
                  title: 'Project Memory',
                  description: 'Automatically document decisions and link them to GitHub issues',
                  command: 'kagura coding end --save-to-github',
                  features: ['GitHub integration', 'Decision tracking', 'Team sharing'],
                  gradient: 'from-orange-500 to-red-500',
                },
              ].map((demo, index) => {
                const Icon = demo.icon;
                return (
                  <div
                    key={demo.title}
                    className="group relative overflow-hidden rounded-3xl border border-gray-200 bg-white p-8 transition-all duration-500 hover:-translate-y-2 hover:border-transparent hover:shadow-2xl"
                    style={{ animationDelay: `${index * 150}ms` }}
                  >
                    {/* Gradient overlay on hover */}
                    <div className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${demo.gradient} opacity-0 transition-opacity duration-500 group-hover:opacity-5`} />

                    {/* Shine effect */}
                    <div className="pointer-events-none absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-1000 group-hover:translate-x-full" />

                    <div className="relative">
                      <div className={`mb-6 inline-flex rounded-2xl bg-gradient-to-br ${demo.gradient} p-4 text-white shadow-lg transition-transform group-hover:scale-110 group-hover:rotate-3`}>
                        <Icon className="h-7 w-7" />
                      </div>

                      <h3 className="mb-3 text-xl font-bold text-gray-900">{demo.title}</h3>
                      <p className="mb-6 text-gray-600">{demo.description}</p>

                      <div className="mb-6 overflow-hidden rounded-xl bg-gradient-to-br from-gray-900 to-gray-800 p-4 shadow-inner">
                        <div className="mb-2 flex gap-1.5">
                          <div className="h-2.5 w-2.5 rounded-full bg-red-400" />
                          <div className="h-2.5 w-2.5 rounded-full bg-yellow-400" />
                          <div className="h-2.5 w-2.5 rounded-full bg-green-400" />
                        </div>
                        <code className="text-sm text-green-400">
                          <span className="text-gray-500">$</span> {demo.command}
                        </code>
                      </div>

                      <div className="space-y-3">
                        {demo.features.map((feature, idx) => (
                          <div 
                            key={feature} 
                            className="flex items-center text-sm font-medium text-gray-700 transition-all"
                            style={{ 
                              animation: mounted ? `slideIn 0.5s ease-out ${idx * 100}ms both` : 'none' 
                            }}
                          >
                            <div className={`mr-3 rounded-full bg-gradient-to-br ${demo.gradient} p-1`}>
                              <Check className="h-3.5 w-3.5 text-white" />
                            </div>
                            <span>{feature}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Features with Bento Grid Style */}
        <section id="features" className="relative overflow-hidden bg-gradient-to-b from-gray-50 to-white px-4 py-24 sm:px-6 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="mb-16 text-center">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand-green-100 to-emerald-100 px-4 py-1.5 text-sm font-semibold text-brand-green-700">
                <Sparkles className="h-4 w-4" />
                <span>Features</span>
              </div>
              <h2 className="mb-4 text-4xl font-bold text-gray-900 sm:text-5xl">Why developers choose Kagura</h2>
              <p className="mx-auto max-w-2xl text-xl text-gray-600">
                Built by developers, for developers. Every feature designed to enhance your AI workflow.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {[
                {
                  icon: Brain,
                  title: 'Infinite Context',
                  description: 'Break free from token limits. Store unlimited context that persists across sessions.',
                  gradient: 'from-blue-500 to-cyan-500',
                  stats: '∞ tokens',
                },
                {
                  icon: Globe,
                  title: 'Universal Compatibility',
                  description: 'Works with Claude, ChatGPT, Gemini, and any AI platform via MCP protocol.',
                  gradient: 'from-purple-500 to-pink-500',
                  stats: '4+ platforms',
                },
                {
                  icon: Zap,
                  title: 'Lightning Fast',
                  description: '50ms retrieval time with intelligent caching and vector search.',
                  gradient: 'from-yellow-500 to-orange-500',
                  stats: '50ms',
                },
                {
                  icon: Shield,
                  title: 'Privacy First',
                  description: 'Self-host or use our cloud. Your data, your control, always encrypted.',
                  gradient: 'from-green-500 to-emerald-500',
                  stats: '100% secure',
                },
                {
                  icon: Code2,
                  title: 'Developer Friendly',
                  description: 'CLI tools, REST API, and MCP integration for seamless workflow integration.',
                  gradient: 'from-red-500 to-pink-500',
                  stats: '3 interfaces',
                },
                {
                  icon: Activity,
                  title: 'Real-time Monitoring',
                  description: 'Track system health, API usage, and memory performance in real-time.',
                  gradient: 'from-indigo-500 to-purple-500',
                  stats: 'Live metrics',
                },
              ].map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <div
                    key={feature.title}
                    className="group relative overflow-hidden rounded-3xl border border-gray-200 bg-white p-8 transition-all duration-500 hover:-translate-y-1 hover:border-transparent hover:shadow-2xl"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <div className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 transition-opacity duration-500 group-hover:opacity-5`} />
                    
                    <div className="relative">
                      <div className="mb-6 flex items-center justify-between">
                        <div className={`inline-flex rounded-2xl bg-gradient-to-br ${feature.gradient} p-3 text-white shadow-lg transition-transform group-hover:scale-110`}>
                          <Icon className="h-6 w-6" />
                        </div>
                        <div className={`rounded-full bg-gradient-to-br ${feature.gradient} bg-opacity-10 px-3 py-1 text-xs font-bold`}>
                          {feature.stats}
                        </div>
                      </div>
                      
                      <h3 className="mb-3 text-lg font-bold text-gray-900">{feature.title}</h3>
                      <p className="text-gray-600">{feature.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Stats with Animated Counters */}
        <section className="relative overflow-hidden border-y border-gray-200/50 bg-white px-4 py-20 sm:px-6 lg:px-8">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-brand-green-50/20 via-transparent to-transparent" />
          
          <div className="relative mx-auto max-w-7xl">
            <div className="grid grid-cols-2 gap-8 text-center md:grid-cols-4">
              {[
                { icon: Database, value: '10,000+', label: 'Memories Stored', color: 'from-blue-500 to-cyan-500' },
                { icon: Clock, value: '50ms', label: 'Retrieval Time', color: 'from-purple-500 to-pink-500' },
                { icon: Workflow, value: '∞', label: 'Context Window', color: 'from-green-500 to-emerald-500' },
                { icon: Shield, value: '100%', label: 'Privacy First', color: 'from-orange-500 to-red-500' },
              ].map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <div 
                    key={stat.label}
                    className="group"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <div className="mb-4 flex justify-center">
                      <div className={`rounded-2xl bg-gradient-to-br ${stat.color} p-4 text-white shadow-lg transition-all group-hover:scale-110 group-hover:shadow-xl`}>
                        <Icon className="h-6 w-6" />
                      </div>
                    </div>
                    <div className={`mb-2 bg-gradient-to-r ${stat.color} bg-clip-text text-5xl font-bold text-transparent transition-all group-hover:scale-110`}>
                      {stat.value}
                    </div>
                    <div className="text-sm font-medium text-gray-600">{stat.label}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Final CTA with Animated Background */}
        <section className="relative overflow-hidden px-4 py-24 sm:px-6 sm:py-32 lg:px-8">
          <div className="absolute inset-0 bg-gradient-to-br from-brand-green-600 via-emerald-600 to-brand-green-700" />
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff15_1px,transparent_1px),linear-gradient(to_bottom,#ffffff15_1px,transparent_1px)] bg-[size:40px_40px]" />
          
          {/* Animated Orbs */}
          <div className="absolute -left-20 -top-20 h-64 w-64 animate-blob rounded-full bg-white/10 mix-blend-overlay blur-3xl" />
          <div className="animation-delay-2000 absolute -right-20 -bottom-20 h-64 w-64 animate-blob rounded-full bg-white/10 mix-blend-overlay blur-3xl" />

          <div className="relative mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold text-white backdrop-blur-sm">
              <Sparkles className="h-4 w-4" />
              <span>Join 10,000+ developers</span>
            </div>

            <h2 className="mb-6 text-4xl font-bold text-white sm:text-5xl">
              Start building your AI memory today
            </h2>
            <p className="mb-10 text-xl leading-relaxed text-white/90">
              Join thousands of developers who never lose their AI context.
              <br className="hidden sm:block" />
              Free to start, powerful enough for production.
            </p>

            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Button
                size="lg"
                onClick={() => router.push('/login')}
                className="group h-14 bg-white px-8 text-base font-semibold text-brand-green-700 shadow-2xl transition-all hover:scale-105 hover:shadow-3xl"
              >
                Get Started Free
                <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Button>
              <div className="flex items-center gap-2 text-sm text-white/90">
                <Shield className="h-4 w-4" />
                <span>No credit card required</span>
              </div>
            </div>

            {/* Social Proof */}
            <div className="mt-12 flex items-center justify-center gap-6">
              <div className="flex -space-x-2">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className="h-10 w-10 rounded-full border-2 border-white bg-gradient-to-br from-gray-300 to-gray-400"
                    style={{ zIndex: 5 - i }}
                  />
                ))}
              </div>
              <div className="text-left">
                <div className="flex items-center gap-1 text-yellow-300">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="h-4 w-4 fill-current" />
                  ))}
                </div>
                <p className="text-sm text-white/80">Loved by 10,000+ developers</p>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-gray-200 bg-gradient-to-b from-white to-gray-50 px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="grid grid-cols-1 gap-12 md:grid-cols-4">
              <div className="md:col-span-1">
                <img src="/kagura-logo.svg" alt="Kagura AI" className="mb-4 h-10 w-auto" />
                <p className="mb-4 text-sm text-gray-600">
                  Universal AI memory for every platform. Never lose context again.
                </p>
                <div className="flex gap-3">
                  <a 
                    href="https://github.com/JFK/kagura-ai" 
                    className="rounded-lg bg-gray-100 p-2 text-gray-600 transition-all hover:bg-brand-green-100 hover:text-brand-green-600"
                  >
                    <Github className="h-5 w-5" />
                  </a>
                </div>
              </div>

              <div>
                <h3 className="mb-4 text-sm font-bold text-gray-900">Product</h3>
                <div className="space-y-3 text-sm">
                  <div><a href="#features" className="text-gray-600 transition-colors hover:text-brand-green-600">Features</a></div>
                  <div><a href="#demo" className="text-gray-600 transition-colors hover:text-brand-green-600">Demo</a></div>
                  <div><a href="https://github.com/JFK/kagura-ai/releases" className="text-gray-600 transition-colors hover:text-brand-green-600">Changelog</a></div>
                </div>
              </div>

              <div>
                <h3 className="mb-4 text-sm font-bold text-gray-900">Resources</h3>
                <div className="space-y-3 text-sm">
                  <div><a href="https://docs.kagura-ai.com" className="text-gray-600 transition-colors hover:text-brand-green-600">Documentation</a></div>
                  <div><a href="https://docs.kagura-ai.com/api-reference" className="text-gray-600 transition-colors hover:text-brand-green-600">API Reference</a></div>
                  <div><a href="https://github.com/JFK/kagura-ai/tree/main/examples" className="text-gray-600 transition-colors hover:text-brand-green-600">Examples</a></div>
                </div>
              </div>

              <div>
                <h3 className="mb-4 text-sm font-bold text-gray-900">Community</h3>
                <div className="space-y-3 text-sm">
                  <div><a href="https://github.com/JFK/kagura-ai" className="text-gray-600 transition-colors hover:text-brand-green-600">GitHub</a></div>
                  <div><a href="https://twitter.com/kagura_ai" className="text-gray-600 transition-colors hover:text-brand-green-600">Twitter</a></div>
                  <div><a href="https://github.com/JFK/kagura-ai/discussions" className="text-gray-600 transition-colors hover:text-brand-green-600">Discussions</a></div>
                </div>
              </div>
            </div>

            <div className="mt-12 border-t border-gray-200 pt-8">
              <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span>© 2025 Kagura AI v4.4.0</span>
                  <span className="text-gray-400">•</span>
                  <span>Made with ❤️ by developers</span>
                </div>
                <div className="flex gap-6 text-sm">
                  <a href="#" className="text-gray-600 transition-colors hover:text-brand-green-600">Privacy</a>
                  <a href="#" className="text-gray-600 transition-colors hover:text-brand-green-600">Terms</a>
                  <a href="https://github.com/JFK/kagura-ai/blob/main/LICENSE" className="text-gray-600 transition-colors hover:text-brand-green-600">License</a>
                </div>
              </div>
            </div>
          </div>
        </footer>

        {/* Custom Animations CSS */}
        <style jsx global>{`
          @keyframes gradient {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
          }
          
          @keyframes blob {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(30px, -50px) scale(1.1); }
            66% { transform: translate(-20px, 20px) scale(0.9); }
          }
          
          @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
          }
          
          @keyframes draw {
            to { stroke-dashoffset: 0; }
          }
          
          @keyframes fade-in {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
          }
          
          @keyframes slideIn {
            from { opacity: 0; transform: translateX(-10px); }
            to { opacity: 1; transform: translateX(0); }
          }
          
          .animate-gradient { animation: gradient 3s ease infinite; }
          .animate-blob { animation: blob 7s ease-in-out infinite; }
          .animate-float { animation: float 3s ease-in-out infinite; }
          .animate-draw { 
            stroke-dasharray: 200; 
            stroke-dashoffset: 200; 
            animation: draw 2s ease-in-out forwards; 
          }
          .animate-fade-in { animation: fade-in 0.8s ease-out; }
          .animation-delay-2000 { animation-delay: 2s; }
          .animation-delay-4000 { animation-delay: 4s; }
        `}</style>
      </div>
    );
  }

  return null;
}
