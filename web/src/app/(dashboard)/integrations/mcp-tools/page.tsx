'use client';

/**
 * MCP Tools Page
 *
 * Displays available MCP tools for ChatGPT Connector and Claude Code integration.
 */

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Wrench, CheckCircle, XCircle } from 'lucide-react';

interface MCPTool {
  name: string;
  category: string;
  remote_capable: boolean;
  description: string;
}

interface MCPToolsResponse {
  tools: MCPTool[];
  total: number;
  categories: string[];
}

export default function MCPToolsPage() {
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    async function fetchTools() {
      try {
        const response = await fetch('/api/v1/mcp/tools');
        const data: MCPToolsResponse = await response.json();
        setTools(data.tools);
      } catch (error) {
        console.error('Failed to fetch MCP tools:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchTools();
  }, []);

  const categories = ['all', ...new Set(tools.map(t => t.category))];
  const filteredTools = selectedCategory === 'all'
    ? tools
    : tools.filter(t => t.category === selectedCategory);

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">MCP Tools</h1>
          <p className="text-slate-500 mt-2">Loading available tools...</p>
        </div>
        <div className="animate-pulse space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Wrench className="h-8 w-8 text-brand-green-600" />
          <h1 className="text-3xl font-bold tracking-tight">MCP Tools</h1>
        </div>
        <p className="text-slate-500 dark:text-slate-400">
          {tools.length} tools available for ChatGPT Connector and Claude Code integration
        </p>
      </div>

      {/* Category Filter */}
      <div className="flex gap-2 flex-wrap">
        {categories.map(cat => (
          <Badge
            key={cat}
            variant={selectedCategory === cat ? 'default' : 'outline'}
            className={`cursor-pointer ${selectedCategory === cat ? 'bg-brand-green-600' : ''}`}
            onClick={() => setSelectedCategory(cat)}
          >
            {cat === 'all' ? 'All' : cat.charAt(0).toUpperCase() + cat.slice(1)}
          </Badge>
        ))}
      </div>

      {/* Tools Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredTools.map(tool => (
          <Card key={tool.name} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <CardTitle className="text-base font-mono">{tool.name}</CardTitle>
                {tool.remote_capable ? (
                  <CheckCircle className="h-4 w-4 text-green-600" title="Remote-capable" />
                ) : (
                  <XCircle className="h-4 w-4 text-gray-400" title="Local-only" />
                )}
              </div>
              <Badge variant="outline" className="w-fit">
                {tool.category}
              </Badge>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-sm">
                {tool.description}
              </CardDescription>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Statistics</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <div>
            <div className="text-2xl font-bold">{tools.length}</div>
            <p className="text-sm text-slate-500">Total Tools</p>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-600">
              {tools.filter(t => t.remote_capable).length}
            </div>
            <p className="text-sm text-slate-500">Remote-capable</p>
          </div>
          <div>
            <div className="text-2xl font-bold">{categories.length - 1}</div>
            <p className="text-sm text-slate-500">Categories</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
