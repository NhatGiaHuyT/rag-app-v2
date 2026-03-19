"use client";

import { useEffect, useMemo, useState } from "react";
import DashboardLayout from "@/components/layout/dashboard-layout";
import { api, ApiError } from "@/lib/api";

interface AnalyticsPoint {
  label: string;
  value: number;
}

interface AnalyticsPayload {
  summary: Record<string, number>;
  activity: AnalyticsPoint[];
  recent_feedback: Array<{
    id: number;
    rating: string;
    comment?: string | null;
    updated_at: string;
  }>;
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/api/analytics/me")
      .then(setData)
      .catch((fetchError) =>
        setError(fetchError instanceof ApiError ? fetchError.message : "Failed to load analytics")
      );
  }, []);

  const maxValue = useMemo(() => Math.max(...(data?.activity.map((item) => item.value) || [1])), [data]);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">
            Track your knowledge coverage, chat volume, and message activity.
          </p>
        </div>

        {error && <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-destructive">{error}</div>}

        {data && (
          <>
            <div className="grid gap-4 md:grid-cols-5">
              {Object.entries(data.summary).map(([key, value]) => (
                <div key={key} className="rounded-2xl border bg-card p-5">
                  <p className="text-sm capitalize text-muted-foreground">{key.replace(/_/g, " ")}</p>
                  <p className="mt-3 text-3xl font-bold">{value}</p>
                </div>
              ))}
            </div>

            <div className="rounded-2xl border bg-card p-6">
              <h2 className="text-lg font-semibold">Message activity over the last 7 days</h2>
              <div className="mt-6 grid grid-cols-7 gap-3">
                {data.activity.map((point) => (
                  <div key={point.label} className="space-y-3 text-center">
                    <div className="flex h-44 items-end justify-center rounded-xl bg-muted/50 p-3">
                      <div
                        className="w-full rounded-lg bg-primary/80 transition-all"
                        style={{ height: `${Math.max(12, (point.value / maxValue) * 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">{point.label}</p>
                    <p className="text-sm font-medium">{point.value}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border bg-card p-6">
              <h2 className="text-lg font-semibold">Recent feedback</h2>
              <div className="mt-4 space-y-3">
                {data.recent_feedback.length === 0 && (
                  <p className="text-sm text-muted-foreground">No feedback submitted yet.</p>
                )}
                {data.recent_feedback.map((entry) => (
                  <div key={entry.id} className="rounded-xl border bg-background p-4">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium">
                        {entry.rating === "up" ? "Helpful answer" : "Needs improvement"}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(entry.updated_at).toLocaleString()}
                      </p>
                    </div>
                    {entry.comment && <p className="mt-2 text-sm text-muted-foreground">{entry.comment}</p>}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
