"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/layout/dashboard-layout";
import {
  ArrowRight,
  BarChart3,
  Book,
  Brain,
  MessageSquare,
  Plus,
  ShieldCheck,
  Sparkles,
  Upload,
} from "lucide-react";
import { api } from "@/lib/api";

interface AnalyticsPayload {
  summary: Record<string, number>;
}

interface UserPayload {
  is_superuser: boolean;
  is_expert: boolean;
  role?: string;
}

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsPayload | null>(null);
  const [user, setUser] = useState<UserPayload | null>(null);

  useEffect(() => {
    Promise.all([api.get("/api/analytics/me"), api.get("/api/auth/me")])
      .then(([analyticsData, userData]) => {
        setAnalytics(analyticsData);
        setUser(userData);
      })
      .catch(() => undefined);
  }, []);

  return (
    <DashboardLayout>
      <div className="p-8 max-w-7xl mx-auto space-y-10">
        <div className="rounded-[2rem] bg-[radial-gradient(circle_at_top_left,_rgba(17,94,89,0.18),_transparent_35%),linear-gradient(135deg,#f7f7ef_0%,#eef7f5_45%,#f4efe7_100%)] p-8 shadow-sm">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-4">
              <p className="text-sm uppercase tracking-[0.25em] text-teal-700">Operational Hub</p>
              <h1 className="max-w-3xl text-4xl font-bold tracking-tight text-slate-900">
                Build cleaner knowledge workflows with profiles, permissions, analytics, and expert review.
              </h1>
              <p className="max-w-2xl text-slate-600">
                User accounts can chat naturally, review history, leave feedback, and read only the internal documents they are allowed to access.
                Admin accounts manage documents, permissions, analytics, and can route flagged answers to experts for manual review.
              </p>
            </div>
            <a
              href="/dashboard/chat/new"
              className="inline-flex items-center justify-center rounded-full bg-teal-700 px-6 py-3 text-sm font-medium text-white shadow-lg shadow-teal-800/10 transition hover:bg-teal-800"
            >
              <Sparkles className="mr-2 h-4 w-4" />
              Start a Live Chat
            </a>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-5">
          {analytics &&
            Object.entries(analytics.summary).map(([key, value]) => (
              <div key={key} className="rounded-2xl border bg-card p-5">
                <p className="text-sm capitalize text-muted-foreground">{key.replace(/_/g, " ")}</p>
                <p className="mt-2 text-3xl font-bold">{value}</p>
              </div>
            ))}
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <a href="/dashboard/knowledge/new" className="rounded-2xl border bg-card p-6 transition hover:-translate-y-0.5 hover:shadow-md">
            <Brain className="h-8 w-8 text-teal-700" />
            <h2 className="mt-5 text-xl font-semibold">Create knowledge bases</h2>
            <p className="mt-2 text-sm text-muted-foreground">Organize new domains and assign access before documents go live.</p>
          </a>
          <a href="/dashboard/analytics" className="rounded-2xl border bg-card p-6 transition hover:-translate-y-0.5 hover:shadow-md">
            <BarChart3 className="h-8 w-8 text-orange-600" />
            <h2 className="mt-5 text-xl font-semibold">Track usage</h2>
            <p className="mt-2 text-sm text-muted-foreground">See your document, chat, message, and feedback activity at a glance.</p>
          </a>
          <a href="/dashboard/profile" className="rounded-2xl border bg-card p-6 transition hover:-translate-y-0.5 hover:shadow-md">
            <ShieldCheck className="h-8 w-8 text-indigo-600" />
            <h2 className="mt-5 text-xl font-semibold">Maintain your profile</h2>
            <p className="mt-2 text-sm text-muted-foreground">Keep your account details current and surface expert status when applicable.</p>
          </a>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border bg-card p-8">
            <h2 className="text-2xl font-semibold">Quick actions</h2>
            <div className="mt-6 space-y-4">
              <a href="/dashboard/knowledge" className="flex items-center justify-between rounded-xl border px-4 py-4 hover:bg-accent/40">
                <div className="flex items-center gap-3">
                  <Book className="h-5 w-5 text-teal-700" />
                  <span>Manage knowledge base permissions</span>
                </div>
                <ArrowRight className="h-4 w-4" />
              </a>
              <a href="/dashboard/chat" className="flex items-center justify-between rounded-xl border px-4 py-4 hover:bg-accent/40">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-5 w-5 text-orange-600" />
                  <span>Review conversation history and feedback</span>
                </div>
                <ArrowRight className="h-4 w-4" />
              </a>
              <a href="/dashboard/knowledge/new" className="flex items-center justify-between rounded-xl border px-4 py-4 hover:bg-accent/40">
                <div className="flex items-center gap-3">
                  <Upload className="h-5 w-5 text-indigo-600" />
                  <span>Prepare a new document workspace</span>
                </div>
                <ArrowRight className="h-4 w-4" />
              </a>
            </div>
          </div>

          <div className="rounded-2xl border bg-card p-8">
            <h2 className="text-2xl font-semibold">Workspace status</h2>
            <div className="mt-6 space-y-5 text-sm text-muted-foreground">
              <p>The chat experience now renders responses live instead of waiting for navigation or refresh.</p>
              <p>Assistant answers can collect feedback, and expert reviewers can publish answer overrides directly in the conversation view.</p>
              {(user?.is_superuser || user?.role === "admin" || user?.role === "super_admin") && (
                <a href="/dashboard/admin" className="inline-flex items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white">
                  <Plus className="mr-2 h-4 w-4" />
                  Open Admin Dashboard
                </a>
              )}
              {(user?.is_expert || user?.role === "expert" || user?.role === "super_admin") && (
                <a href="/dashboard/expert-review" className="inline-flex items-center rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700">
                  <Plus className="mr-2 h-4 w-4" />
                  Open Expert Review
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
