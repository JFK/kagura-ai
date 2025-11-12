/**
 * API Key Stats Dialog
 *
 * Issue #655 - Display usage statistics for API keys
 */

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, BarChart3 } from 'lucide-react';
import { getAPIKeyStats } from '@/lib/api-keys';
import type { APIKeyStats } from '@/lib/types/api-key';

interface APIKeyStatsDialogProps {
  isOpen: boolean;
  keyId: number;
  keyName: string;
  onClose: () => void;
}

export function APIKeyStatsDialog({
  isOpen,
  keyId,
  keyName,
  onClose,
}: APIKeyStatsDialogProps) {
  const [stats, setStats] = useState<APIKeyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchStats();
    }
  }, [isOpen, keyId]);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await getAPIKeyStats(keyId, 30);
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch API key stats:', err);
      setError(err instanceof Error ? err.message : 'Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Usage Statistics: {keyName}
          </DialogTitle>
          <DialogDescription>
            Request statistics for the past 30 days
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4 max-h-[500px] overflow-y-auto">
          {loading && (
            <div className="flex items-center justify-center h-32">
              <div className="flex flex-col items-center gap-2">
                <div className="h-8 w-8 rounded-full border-4 border-slate-200 border-t-slate-600 animate-spin" />
                <p className="text-sm text-slate-500">Loading statistics...</p>
              </div>
            </div>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {stats && !loading && (
            <>
              {/* Summary */}
              <div className="grid grid-cols-3 gap-4 p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
                <div>
                  <p className="text-xs text-slate-500">Total Requests</p>
                  <p className="text-2xl font-bold">{stats.total_requests.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Period Start</p>
                  <p className="text-sm font-medium">{stats.period_start || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Period End</p>
                  <p className="text-sm font-medium">{stats.period_end || 'N/A'}</p>
                </div>
              </div>

              {/* Daily breakdown */}
              {stats.total_requests === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm text-slate-500">No usage data available</p>
                  <p className="text-xs text-slate-400 mt-1">
                    This key hasn't been used in the past 30 days
                  </p>
                </div>
              ) : (
                <>
                  <div>
                    <h3 className="text-sm font-medium mb-2">Daily Breakdown</h3>
                    <div className="rounded-lg border border-slate-200 dark:border-slate-800">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Date</TableHead>
                            <TableHead className="text-right">Requests</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {stats.daily_stats
                            .filter((day) => day.count > 0)
                            .reverse()
                            .map((day) => (
                              <TableRow key={day.date}>
                                <TableCell className="font-medium">{day.date}</TableCell>
                                <TableCell className="text-right">{day.count.toLocaleString()}</TableCell>
                              </TableRow>
                            ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>

                  {/* Simple bar chart visualization (CSS-based) */}
                  <div>
                    <h3 className="text-sm font-medium mb-2">Visual Overview</h3>
                    <div className="space-y-1">
                      {stats.daily_stats
                        .filter((day) => day.count > 0)
                        .reverse()
                        .slice(0, 10)
                        .map((day) => {
                          const maxCount = Math.max(...stats.daily_stats.map((d) => d.count));
                          const widthPercent = (day.count / maxCount) * 100;

                          return (
                            <div key={day.date} className="flex items-center gap-2">
                              <span className="text-xs text-slate-500 w-24">{day.date}</span>
                              <div className="flex-1 bg-slate-100 dark:bg-slate-800 rounded-full h-6 relative overflow-hidden">
                                <div
                                  className="bg-blue-500 h-full flex items-center justify-end pr-2"
                                  style={{ width: `${widthPercent}%` }}
                                >
                                  <span className="text-xs text-white font-medium">{day.count}</span>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                </>
              )}
            </>
          )}
        </div>

        <DialogFooter>
          <Button onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
