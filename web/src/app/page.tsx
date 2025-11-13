'use client';

/**
 * Root/Landing Page - Modern Design
 *
 * - Unauthenticated: Shows landing page with "Login with Google"
 * - Authenticated: Redirects to /dashboard
 *
 * Issue #672: UI Polish & Design Enhancement
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import {
  Activity,
  Brain,
  Code2,
  ArrowRight,
  Sparkles,
  Zap,
  Shield,
  Globe,
  CheckCircle,
  ChevronRight,
  Terminal,
  MessageSquare,
  GitBranch
} from 'lucide-react';

export default function LandingPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [activeDemo, setActiveDemo] = useState(0);
  const [typedText, setTypedText] = useState('');
  const [showCursor, setShowCursor] = useState(true);

  // Typing animation effect
  const fullText = "Never lose your AI context again.";
  useEffect(() => {
    if (!user && !isLoading) {
      let index = 0;
      const interval = setInterval(() => {
        if (index <= fullText.length) {
          setTypedText(fullText.slice(0, index));
          index++;
        } else {
          clearInterval(interval);
        }
      }, 50);

      // Cursor blink
      const cursorInterval = setInterval(() => {
        setShowCursor(prev => !prev);
      }, 500);

      return () => {
        clearInterval(interval);
        clearInterval(cursorInterval);
      };
    }
  }, [user, isLoading]);

  // Demo carousel rotation
  useEffect(() => {
    if (!user && !isLoading) {
      const interval = setInterval(() => {
        setActiveDemo(prev => (prev + 1) % 3);
      }, 4000);
      return () => clearInterval(interval);
    }
  }, [user, isLoading]);

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (!isLoading && user) {
      router.push('/dashboard');
    }
  }, [user, isLoading, router]);

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-black">
        <div className="text-center">
          {/* Futuristic Loading Animation */}
          <div className="relative w-32 h-32 mx-auto mb-8">
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 opacity-20 animate-pulse" />
            <div className="absolute inset-2 rounded-full bg-black" />
            <img
              src="/kagura-logo.svg"
              alt="Loading"
              className="absolute inset-4 w-24 h-24 animate-float"
            />
            {/* Rotating ring */}
            <svg className="absolute inset-0 w-32 h-32 animate-spin-slow" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="url(#gradient)"
                strokeWidth="2"
                strokeLinecap="round"
                strokeDasharray="20 10"
              />
              <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="50%" stopColor="#a855f7" />
                  <stop offset="100%" stopColor="#ec4899" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-center space-x-1">
              {['Initializing', 'Memory', 'Cloud'].map((word, i) => (
                <span
                  key={word}
                  className="text-sm font-mono text-gray-400 animate-pulse"
                  style={{ animationDelay: `${i * 0.2}s` }}
                >
                  {word}
                </span>
              ))}
            </div>
            <div className="flex items-center justify-center space-x-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-2 h-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.1}s` }}
                />
              ))}
            </div>
          </div>
        </div>

        <style jsx>{`
          @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-10px) rotate(5deg); }
          }
          @keyframes spin-slow {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          .animate-float {
            animation: float 3s ease-in-out infinite;
          }
          .animate-spin-slow {
            animation: spin-slow 3s linear infinite;
          }
        `}</style>
      </main>
    );
  }

  // Show landing page for unauthenticated users
  if (!user) {
    const demoExamples = [
      {
        icon: <Terminal className="h-5 w-5" />,
        title: "Coding Sessions",
        description: "Track every decision, error, and solution across your development workflow",
        preview: "kagura coding start --project my-app\n> Session started: Implementing OAuth2\n> Files tracked: 12\n> Errors resolved: 3"
      },
      {
        icon: <MessageSquare className="h-5 w-5" />,
        title: "AI Conversations",
        description: "Preserve context across Claude, ChatGPT, and Gemini sessions",
        preview: "kagura memory store --tags ai,architecture\n> Stored: System design discussion\n> Retrievable across all AI platforms\n> Context preserved permanently"
      },
      {
        icon: <GitBranch className="h-5 w-5" />,
        title: "Project Memory",
        description: "Automatically document decisions and link them to GitHub issues",
        preview: "kagura coding end --save-to-github\n> Summary posted to Issue #672\n> Design decisions documented\n> Knowledge graph updated"
      }
    ];

    const stats = [
      { value: "10K+", label: "Memories Stored", gradient: "from-blue-600 to-cyan-600" },
      { value: "50ms", label: "Retrieval Time", gradient: "from-purple-600 to-pink-600" },
      { value: "∞", label: "Context Window", gradient: "from-orange-600 to-red-600" },
      { value: "100%", label: "Privacy First", gradient: "from-green-600 to-emerald-600" }
    ];

    return (
      <main className="min-h-screen bg-black text-white overflow-hidden">
        {/* Animated background grid */}
        <div className="fixed inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none" />

        {/* Gradient orbs */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -left-40 w-80 h-80 bg-purple-700 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-700 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
          <div className="absolute -bottom-40 left-20 w-80 h-80 bg-pink-700 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000" />
        </div>

        <div className="relative z-10">
          {/* Navigation */}
          <nav className="container mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-3">
                <img src="/kagura-logo.svg" alt="Kagura AI" className="h-10 w-10" />
                <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  Kagura AI
                </span>
              </div>
              <div className="flex items-center space-x-6">
                <a href="#features" className="text-gray-400 hover:text-white transition-colors hidden sm:block">
                  Features
                </a>
                <a href="#demo" className="text-gray-400 hover:text-white transition-colors hidden sm:block">
                  Demo
                </a>
                <Button
                  variant="outline"
                  className="border-gray-700 text-gray-300 hover:bg-gray-900 hover:text-white"
                  onClick={() => router.push('/login')}
                >
                  Sign In
                </Button>
              </div>
            </div>
          </nav>

          {/* Hero Section */}
          <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
            <div className="text-center max-w-5xl mx-auto">
              {/* Badge */}
              <div className="inline-flex items-center space-x-2 bg-gray-900/50 backdrop-blur-lg border border-gray-800 rounded-full px-4 py-2 mb-8">
                <Sparkles className="h-4 w-4 text-yellow-500" />
                <span className="text-sm text-gray-300">v4.4.0 - Now with MCP Protocol Support</span>
              </div>

              {/* Main heading with typing effect */}
              <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-6">
                <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent animate-gradient">
                  Universal AI Memory
                </span>
                <br />
                <span className="text-gray-300">for Every Platform</span>
              </h1>

              <p className="text-xl sm:text-2xl text-gray-400 mb-8 h-8">
                {typedText}
                {showCursor && <span className="text-purple-400">|</span>}
              </p>

              <p className="text-base sm:text-lg text-gray-500 mb-10 max-w-2xl mx-auto">
                Store, retrieve, and share context seamlessly across Claude, ChatGPT, Gemini,
                and any AI platform. Your knowledge, always accessible.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4 mb-16">
                <Button
                  size="lg"
                  className="w-full sm:w-auto px-8 py-6 text-lg font-semibold bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-xl hover:shadow-2xl hover:shadow-purple-500/25 transition-all duration-300 transform hover:scale-105 group"
                  onClick={() => router.push('/login')}
                >
                  <svg className="w-6 h-6 mr-3" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                  </svg>
                  Start Free with Google
                  <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  className="w-full sm:w-auto px-8 py-6 text-lg border-gray-700 text-gray-300 hover:bg-gray-900 hover:text-white hover:border-gray-600"
                >
                  <Code2 className="mr-2 h-5 w-5" />
                  View on GitHub
                </Button>
              </div>

              {/* Live Demo Preview */}
              <div className="relative max-w-4xl mx-auto" id="demo">
                <div className="bg-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-800 p-1">
                  <div className="bg-gray-950 rounded-xl p-6">
                    {/* Terminal header */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-red-500 rounded-full" />
                        <div className="w-3 h-3 bg-yellow-500 rounded-full" />
                        <div className="w-3 h-3 bg-green-500 rounded-full" />
                      </div>
                      <div className="flex space-x-2">
                        {demoExamples.map((demo, index) => (
                          <button
                            key={index}
                            onClick={() => setActiveDemo(index)}
                            className={`px-3 py-1 rounded text-xs transition-all ${
                              activeDemo === index
                                ? 'bg-purple-600 text-white'
                                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                            }`}
                          >
                            {demo.icon}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Demo content */}
                    <div className="space-y-3">
                      <div className="flex items-center space-x-2 text-purple-400">
                        {demoExamples[activeDemo].icon}
                        <span className="font-mono text-sm">{demoExamples[activeDemo].title}</span>
                      </div>
                      <p className="text-gray-400 text-sm">{demoExamples[activeDemo].description}</p>
                      <pre className="font-mono text-xs text-green-400 bg-black/50 rounded p-3 overflow-x-auto">
                        {demoExamples[activeDemo].preview}
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Stats Section */}
          <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 max-w-4xl mx-auto">
              {stats.map((stat, index) => (
                <div
                  key={index}
                  className="text-center group hover:scale-105 transition-transform duration-300"
                >
                  <div className={`text-3xl sm:text-4xl font-bold bg-gradient-to-r ${stat.gradient} bg-clip-text text-transparent mb-2`}>
                    {stat.value}
                  </div>
                  <div className="text-sm text-gray-500">{stat.label}</div>
                </div>
              ))}
            </div>
          </section>

          {/* Features Section */}
          <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-16" id="features">
            <div className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl font-bold mb-4">
                Why Developers Choose Kagura
              </h2>
              <p className="text-gray-400 max-w-2xl mx-auto">
                Built by developers, for developers. Every feature designed to enhance your AI workflow.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
              {[
                {
                  icon: <Brain className="h-8 w-8" />,
                  title: "Infinite Context",
                  description: "Break free from token limits. Store unlimited context that persists across sessions.",
                  gradient: "from-blue-500 to-cyan-500"
                },
                {
                  icon: <Globe className="h-8 w-8" />,
                  title: "Universal Compatibility",
                  description: "Works with Claude, ChatGPT, Gemini, and any AI platform via MCP protocol.",
                  gradient: "from-purple-500 to-pink-500"
                },
                {
                  icon: <Zap className="h-8 w-8" />,
                  title: "Lightning Fast",
                  description: "50ms retrieval time with intelligent caching and vector search.",
                  gradient: "from-yellow-500 to-orange-500"
                },
                {
                  icon: <Shield className="h-8 w-8" />,
                  title: "Privacy First",
                  description: "Self-host or use our cloud. Your data, your control, always encrypted.",
                  gradient: "from-green-500 to-emerald-500"
                },
                {
                  icon: <Code2 className="h-8 w-8" />,
                  title: "Developer Friendly",
                  description: "CLI tools, REST API, and MCP integration for seamless workflow integration.",
                  gradient: "from-red-500 to-pink-500"
                },
                {
                  icon: <Activity className="h-8 w-8" />,
                  title: "Real-time Monitoring",
                  description: "Track system health, API usage, and memory performance in real-time.",
                  gradient: "from-indigo-500 to-purple-500"
                }
              ].map((feature, index) => (
                <div
                  key={index}
                  className="group relative bg-gray-900/30 backdrop-blur-lg rounded-2xl p-6 border border-gray-800 hover:border-gray-700 transition-all duration-300 hover:transform hover:-translate-y-1"
                >
                  <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${feature.gradient} mb-4 group-hover:scale-110 transition-transform duration-300`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-gray-400 text-sm">{feature.description}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Use Cases */}
          <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-16 mb-20">
            <div className="max-w-4xl mx-auto">
              <div className="text-center mb-12">
                <h2 className="text-3xl sm:text-4xl font-bold mb-4">
                  Perfect For Your Workflow
                </h2>
              </div>

              <div className="space-y-4">
                {[
                  {
                    title: "AI-Assisted Development",
                    description: "Keep your entire project context alive across coding sessions",
                    benefits: ["Track decisions", "Remember errors", "Share with team"]
                  },
                  {
                    title: "Research & Analysis",
                    description: "Build a persistent knowledge base from all your AI conversations",
                    benefits: ["Cross-reference", "Semantic search", "Export anytime"]
                  },
                  {
                    title: "Team Collaboration",
                    description: "Share context and decisions automatically with your team",
                    benefits: ["GitHub integration", "Project memory", "Real-time sync"]
                  }
                ].map((useCase, index) => (
                  <div
                    key={index}
                    className="group bg-gray-900/30 backdrop-blur-lg rounded-xl p-6 border border-gray-800 hover:border-purple-600/50 transition-all duration-300"
                  >
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg flex items-center justify-center">
                        <CheckCircle className="h-6 w-6 text-white" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold mb-2">{useCase.title}</h3>
                        <p className="text-gray-400 text-sm mb-3">{useCase.description}</p>
                        <div className="flex flex-wrap gap-2">
                          {useCase.benefits.map((benefit, i) => (
                            <span
                              key={i}
                              className="text-xs px-3 py-1 bg-gray-800 rounded-full text-gray-300"
                            >
                              {benefit}
                            </span>
                          ))}
                        </div>
                      </div>
                      <ChevronRight className="h-5 w-5 text-gray-600 group-hover:text-purple-400 transition-colors" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* Final CTA */}
          <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-20 mb-12">
            <div className="max-w-4xl mx-auto text-center">
              <div className="bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-pink-600/20 backdrop-blur-xl rounded-3xl p-12 border border-gray-800">
                <h2 className="text-3xl sm:text-4xl font-bold mb-6">
                  Start Building Your AI Memory Today
                </h2>
                <p className="text-gray-400 mb-8 max-w-2xl mx-auto">
                  Join thousands of developers who never lose their AI context.
                  Free to start, powerful enough for production.
                </p>
                <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4">
                  <Button
                    size="lg"
                    className="w-full sm:w-auto px-10 py-6 text-lg font-semibold bg-white text-black hover:bg-gray-200 shadow-xl transition-all duration-300 transform hover:scale-105"
                    onClick={() => router.push('/login')}
                  >
                    <Sparkles className="mr-2 h-5 w-5" />
                    Get Started Free
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                  <div className="text-sm text-gray-500">
                    No credit card required
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Footer */}
          <footer className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 border-t border-gray-800">
            <div className="flex flex-col sm:flex-row items-center justify-between">
              <div className="flex items-center space-x-3 mb-4 sm:mb-0">
                <img src="/kagura-icon.svg" alt="Kagura AI" className="h-8 w-8" />
                <span className="text-sm text-gray-400">© 2025 Kagura AI v4.4.0</span>
              </div>
              <div className="flex space-x-6 text-sm">
                <a href="#" className="text-gray-400 hover:text-white transition-colors">Documentation</a>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">GitHub</a>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">Discord</a>
              </div>
            </div>
          </footer>
        </div>

        {/* Custom animations */}
        <style jsx>{`
          @keyframes blob {
            0%, 100% {
              transform: translate(0px, 0px) scale(1);
            }
            33% {
              transform: translate(30px, -50px) scale(1.1);
            }
            66% {
              transform: translate(-20px, 20px) scale(0.9);
            }
          }
          @keyframes gradient {
            0%, 100% {
              background-position: 0% 50%;
            }
            50% {
              background-position: 100% 50%;
            }
          }
          .animate-blob {
            animation: blob 7s infinite;
          }
          .animation-delay-2000 {
            animation-delay: 2s;
          }
          .animation-delay-4000 {
            animation-delay: 4s;
          }
          .animate-gradient {
            background-size: 200% 200%;
            animation: gradient 3s ease infinite;
          }
        `}</style>
      </main>
    );
  }

  // Should not reach here (redirect in useEffect)
  return null;
}