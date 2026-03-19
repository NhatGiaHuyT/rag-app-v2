"use client";

import { useEffect, useMemo, useState } from "react";
import DashboardLayout from "@/components/layout/dashboard-layout";
import { api, ApiError } from "@/lib/api";

interface AdminOverview {
  summary: Record<string, number>;
  activity: Array<{ label: string; value: number }>;
  top_users: Array<{ id: number; username: string; full_name?: string | null; chat_count: number }>;
  frequent_topics: Array<{ topic: string; count: number }>;
  peak_hours: Array<{ hour: number; count: number }>;
  feedback_summary: Record<string, number>;
  document_effectiveness: Array<{ id: number; file_name: string; query_count: number; status: string }>;
}

interface AdminUser {
  id: number;
  email: string;
  username: string;
  full_name?: string | null;
  role: string;
  feature_flags: Record<string, boolean>;
  is_active: boolean;
  is_expert: boolean;
  suspended_until?: string | null;
  knowledge_base_count: number;
  chat_count: number;
}

interface FlaggedAnswer {
  feedback_id: number;
  message_id: number;
  chat_id: number;
  chat_title: string;
  question: string;
  answer: string;
  comment?: string | null;
  status: string;
  requester_username: string;
  expert_assignee_id?: number | null;
  expert_assignee_name?: string | null;
}

export default function AdminPage() {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [accessLogs, setAccessLogs] = useState<any[]>([]);
  const [manualQa, setManualQa] = useState<any[]>([]);
  const [flaggedAnswers, setFlaggedAnswers] = useState<FlaggedAnswer[]>([]);
  const [systemConfig, setSystemConfig] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [newUser, setNewUser] = useState({ email: "", username: "", password: "", full_name: "", role: "user" });
  const [manualQuestion, setManualQuestion] = useState("");
  const [manualAnswer, setManualAnswer] = useState("");

  const load = async () => {
    try {
      const [overviewData, usersData, documentsData, kbData, alertsData, auditData, accessData, manualQaData, flaggedData, configData] =
        await Promise.all([
          api.get("/api/admin/overview"),
          api.get("/api/admin/users"),
          api.get("/api/admin/documents"),
          api.get("/api/admin/knowledge-bases"),
          api.get("/api/admin/alerts"),
          api.get("/api/admin/audit-logs"),
          api.get("/api/admin/access-logs"),
          api.get("/api/admin/quality/manual-qa"),
          api.get("/api/admin/quality/flagged-answers"),
          api.get("/api/admin/system-config"),
        ]);
      setOverview(overviewData);
      setUsers(usersData.users);
      setDocuments(documentsData);
      setKnowledgeBases(kbData);
      setAlerts(alertsData);
      setAuditLogs(auditData);
      setAccessLogs(accessData);
      setManualQa(manualQaData);
      setFlaggedAnswers(flaggedData);
      setSystemConfig(configData);
      setError(null);
    } catch (fetchError) {
      setError(fetchError instanceof ApiError ? fetchError.message : "Failed to load admin workspace");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const failedAccessCount = useMemo(() => accessLogs.filter((entry) => !entry.success).length, [accessLogs]);

  const updateUser = async (user: AdminUser, payload: Record<string, unknown>) => {
    try {
      await api.put(`/api/admin/users/${user.id}`, payload);
      await load();
    } catch (saveError) {
      setError(saveError instanceof ApiError ? saveError.message : "Failed to update user");
    }
  };

  const assignToExpert = async (feedbackId: number, expertUserId: number) => {
    if (!expertUserId) {
      return;
    }
    try {
      await api.post(`/api/admin/quality/flagged-answers/${feedbackId}/assign`, {
        expert_user_id: expertUserId,
      });
      await load();
    } catch (saveError) {
      setError(saveError instanceof ApiError ? saveError.message : "Failed to assign expert");
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Admin Workspace</h1>
          <p className="text-muted-foreground">Manage users, documents, quality feedback, and expert review assignments.</p>
        </div>

        {error && <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-destructive">{error}</div>}

        {overview && (
          <>
            <div className="grid gap-4 md:grid-cols-4 xl:grid-cols-8">
              {Object.entries(overview.summary).map(([key, value]) => (
                <div key={key} className="rounded-2xl border bg-card p-5">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">{key.replace(/_/g, " ")}</p>
                  <p className="mt-2 text-2xl font-bold">{value}</p>
                </div>
              ))}
            </div>

            <div className="grid gap-6 xl:grid-cols-2">
              <div className="rounded-2xl border bg-card p-6">
                <h2 className="text-lg font-semibold">Monitoring and Analytics</h2>
                <div className="mt-4 grid grid-cols-7 gap-2">
                  {overview.activity.map((point) => (
                    <div key={point.label} className="rounded-xl bg-muted/50 p-3 text-center">
                      <p className="text-xl font-bold">{point.value}</p>
                      <p className="text-xs text-muted-foreground">{point.label}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-4 space-y-3 text-sm">
                  <p>Frequent topics: {overview.frequent_topics.map((item) => `${item.topic} (${item.count})`).join(", ") || "none"}</p>
                  <p>Peak hours: {overview.peak_hours.map((item) => `${item.hour}:00 (${item.count})`).join(", ") || "none"}</p>
                  <p>Feedback summary: up {overview.feedback_summary.up || 0}, down {overview.feedback_summary.down || 0}</p>
                </div>
              </div>

              <div className="rounded-2xl border bg-card p-6">
                <h2 className="text-lg font-semibold">Security and Alerts</h2>
                <p className="mt-3 text-sm text-muted-foreground">{alerts.length} alerts and {failedAccessCount} failed access attempts in the latest log sample.</p>
                <div className="mt-4 space-y-3">
                  {alerts.slice(0, 4).map((alert) => (
                    <div key={alert.id} className="rounded-xl border p-4">
                      <p className="font-medium">{alert.message}</p>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">{alert.severity} via {alert.source}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-2">
              <div className="rounded-2xl border bg-card p-6">
                <h2 className="text-lg font-semibold">User and Permission Management</h2>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <input value={newUser.full_name} onChange={(e) => setNewUser((c) => ({ ...c, full_name: e.target.value }))} placeholder="Full name" className="rounded-md border border-input bg-background px-3 py-2 text-sm" />
                  <input value={newUser.username} onChange={(e) => setNewUser((c) => ({ ...c, username: e.target.value }))} placeholder="Username" className="rounded-md border border-input bg-background px-3 py-2 text-sm" />
                  <input value={newUser.email} onChange={(e) => setNewUser((c) => ({ ...c, email: e.target.value }))} placeholder="Email" className="rounded-md border border-input bg-background px-3 py-2 text-sm" />
                  <input value={newUser.password} onChange={(e) => setNewUser((c) => ({ ...c, password: e.target.value }))} placeholder="Temporary password" className="rounded-md border border-input bg-background px-3 py-2 text-sm" />
                  <select value={newUser.role} onChange={(e) => setNewUser((c) => ({ ...c, role: e.target.value }))} className="rounded-md border border-input bg-background px-3 py-2 text-sm">
                    <option value="user">User</option>
                    <option value="expert">Expert</option>
                    <option value="admin">Admin</option>
                    <option value="super_admin">Super Admin</option>
                  </select>
                  <button onClick={() => api.post("/api/admin/users", { ...newUser, feature_flags: { feedback_enabled: true, history_enabled: true, chat_export_enabled: false } }).then(load)} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">Create Account</button>
                </div>
                <div className="mt-6 space-y-3">
                  {users.map((user) => (
                    <div key={user.id} className="rounded-xl border p-4">
                      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                        <div>
                          <p className="font-medium">{user.full_name || user.username}</p>
                          <p className="text-sm text-muted-foreground">{user.email} ? {user.role}</p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <button onClick={() => updateUser(user, { role: user.role === "expert" ? "user" : "expert" })} className="rounded-md border px-3 py-1 text-xs">Toggle Expert</button>
                          <button onClick={() => updateUser(user, { is_active: !user.is_active })} className="rounded-md border px-3 py-1 text-xs">{user.is_active ? "Deactivate" : "Activate"}</button>
                          <button onClick={() => api.post(`/api/admin/users/${user.id}/suspend`, { reason: "Suspended by admin" }).then(load)} className="rounded-md border px-3 py-1 text-xs">Suspend</button>
                          <button onClick={() => api.post(`/api/admin/users/${user.id}/unsuspend`).then(load)} className="rounded-md border px-3 py-1 text-xs">Unsuspend</button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border bg-card p-6">
                <h2 className="text-lg font-semibold">Document and Knowledge Base Management</h2>
                <div className="mt-4 space-y-3">
                  {knowledgeBases.slice(0, 5).map((kb) => (
                    <div key={kb.id} className="rounded-xl border p-4">
                      <p className="font-medium">{kb.name}</p>
                      <p className="text-sm text-muted-foreground">{kb.document_count} docs ? {kb.visibility} ? {kb.department || "unassigned"}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-4 space-y-3">
                  {documents.slice(0, 6).map((document) => (
                    <div key={document.id} className="rounded-xl border p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="font-medium">{document.file_name}</p>
                          <p className="text-sm text-muted-foreground">{document.status} ? {document.access_level} ? queried {document.query_count} times</p>
                        </div>
                        <button onClick={() => api.post(`/api/admin/documents/${document.id}/reindex`).then(load)} className="rounded-md border px-3 py-1 text-xs">Reindex</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-2">
              <div className="rounded-2xl border bg-card p-6">
                <h2 className="text-lg font-semibold">Flagged Answers and Expert Assignment</h2>
                <div className="mt-4 space-y-3">
                  {flaggedAnswers.slice(0, 6).map((item) => (
                    <div key={item.feedback_id} className="rounded-xl border p-4">
                      <p className="font-medium">{item.chat_title}</p>
                      <p className="mt-1 text-sm text-muted-foreground">{item.question}</p>
                      <p className="mt-1 text-xs text-muted-foreground">User feedback: {item.comment || "No comment provided"} ? Status: {item.status}</p>
                      <div className="mt-3 flex flex-wrap items-center gap-2">
                        <select
                          value={item.expert_assignee_id || ""}
                          onChange={(e) => assignToExpert(item.feedback_id, Number(e.target.value))}
                          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                        >
                          <option value="">Select expert</option>
                          {users
                            .filter((user) => user.is_expert || user.role === "expert" || user.role === "admin" || user.role === "super_admin")
                            .map((user) => (
                              <option key={user.id} value={user.id}>{user.full_name || user.username}</option>
                            ))}
                        </select>
                        {item.expert_assignee_name && <span className="text-xs text-muted-foreground">Assigned to: {item.expert_assignee_name}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border bg-card p-6">
                <h2 className="text-lg font-semibold">Manual Q&A and Knowledge Supplement</h2>
                <div className="mt-4 grid gap-3">
                  <input value={manualQuestion} onChange={(e) => setManualQuestion(e.target.value)} placeholder="Manual Q&A question" className="rounded-md border border-input bg-background px-3 py-2 text-sm" />
                  <textarea value={manualAnswer} onChange={(e) => setManualAnswer(e.target.value)} placeholder="Manual Q&A answer" rows={4} className="rounded-md border border-input bg-background px-3 py-2 text-sm" />
                  <button onClick={() => api.post("/api/admin/quality/manual-qa", { question: manualQuestion, answer: manualAnswer, tags: [] }).then(load)} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">Add Manual Q&A</button>
                </div>
                <div className="mt-4 space-y-3">
                  {manualQa.slice(0, 5).map((entry) => (
                    <div key={entry.id} className="rounded-xl border p-4">
                      <p className="font-medium">{entry.question}</p>
                      <p className="mt-1 text-sm text-muted-foreground">{entry.answer}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-2">
              <div className="rounded-2xl border bg-card p-6">
                <h2 className="text-lg font-semibold">Audit and Access Logs</h2>
                <div className="mt-4 space-y-3">
                  {auditLogs.slice(0, 5).map((entry) => (
                    <div key={entry.id} className="rounded-xl border p-4 text-sm">
                      <p className="font-medium">{entry.action}</p>
                      <p className="text-muted-foreground">{entry.entity_type} {entry.entity_id || ""}</p>
                    </div>
                  ))}
                  {accessLogs.slice(0, 5).map((entry) => (
                    <div key={entry.id} className="rounded-xl border p-4 text-sm">
                      <p className="font-medium">{entry.resource_type} / {entry.action}</p>
                      <p className={entry.success ? "text-emerald-600" : "text-rose-600"}>{entry.success ? "allowed" : `blocked: ${entry.failure_reason || "unknown"}`}</p>
                    </div>
                  ))}
                </div>
              </div>

              {systemConfig && (
                <div className="rounded-2xl border bg-card p-6">
                  <h2 className="text-lg font-semibold">System Configuration</h2>
                  <div className="mt-4 grid gap-6 lg:grid-cols-1">
                    <textarea value={JSON.stringify(systemConfig.response_settings, null, 2)} onChange={(e) => setSystemConfig((c: any) => ({ ...c, response_settings: JSON.parse(e.target.value || "{}") }))} rows={5} className="rounded-md border border-input bg-background px-3 py-2 text-xs" />
                    <textarea value={JSON.stringify(systemConfig.feedback_workflow, null, 2)} onChange={(e) => setSystemConfig((c: any) => ({ ...c, feedback_workflow: JSON.parse(e.target.value || "{}") }))} rows={5} className="rounded-md border border-input bg-background px-3 py-2 text-xs" />
                    <textarea value={JSON.stringify(systemConfig.integrations, null, 2)} onChange={(e) => setSystemConfig((c: any) => ({ ...c, integrations: JSON.parse(e.target.value || "{}") }))} rows={5} className="rounded-md border border-input bg-background px-3 py-2 text-xs" />
                  </div>
                  <button onClick={() => api.put("/api/admin/system-config", systemConfig).then(load)} className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">Save System Configuration</button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
