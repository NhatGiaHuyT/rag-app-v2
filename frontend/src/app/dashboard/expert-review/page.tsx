"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/layout/dashboard-layout";
import { api, ApiError } from "@/lib/api";

interface ExpertItem {
  feedback_id: number;
  message_id: number;
  chat_id: number;
  chat_title: string;
  question: string;
  answer: string;
  comment?: string | null;
  status: string;
  requester_username: string;
}

export default function ExpertReviewPage() {
  const [items, setItems] = useState<ExpertItem[]>([]);
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const data = await api.get("/api/feedback/expert/assignments");
      setItems(data);
      setError(null);
    } catch (fetchError) {
      setError(fetchError instanceof ApiError ? fetchError.message : "Failed to load expert queue");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const submitManualAnswer = async (item: ExpertItem) => {
    const content = drafts[item.message_id];
    if (!content?.trim()) {
      return;
    }
    try {
      await api.put(`/api/feedback/messages/${item.message_id}/override`, {
        content,
        note: "Manual expert response after the user flagged the original answer as inaccurate.",
      });
      await load();
    } catch (saveError) {
      setError(saveError instanceof ApiError ? saveError.message : "Failed to submit expert response");
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Expert Review</h1>
          <p className="text-muted-foreground">
            Manually review answers that users reported as inaccurate.
          </p>
        </div>

        {error && <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-destructive">{error}</div>}

        {items.length === 0 ? (
          <div className="rounded-2xl border bg-card p-8 text-sm text-muted-foreground">
            No expert assignments are currently waiting in your queue.
          </div>
        ) : (
          <div className="space-y-5">
            {items.map((item) => (
              <div key={item.feedback_id} className="rounded-2xl border bg-card p-6">
                <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                  <span className="rounded-full bg-muted px-3 py-1">{item.chat_title}</span>
                  <span>Reported by: {item.requester_username}</span>
                  <span>Status: {item.status}</span>
                </div>
                <div className="mt-4 space-y-4">
                  <div>
                    <p className="text-sm font-medium">User question</p>
                    <p className="mt-1 text-sm text-muted-foreground">{item.question}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Current chatbot answer</p>
                    <p className="mt-1 text-sm text-muted-foreground whitespace-pre-wrap">{item.answer}</p>
                  </div>
                  {item.comment && (
                    <div>
                      <p className="text-sm font-medium">User feedback</p>
                      <p className="mt-1 text-sm text-muted-foreground">{item.comment}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm font-medium">Expert response</p>
                    <textarea
                      value={drafts[item.message_id] ?? ""}
                      onChange={(event) =>
                        setDrafts((current) => ({
                          ...current,
                          [item.message_id]: event.target.value,
                        }))
                      }
                      rows={5}
                      className="mt-2 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      placeholder="Write the expert-reviewed answer here..."
                    />
                  </div>
                  <button
                    onClick={() => submitManualAnswer(item)}
                    className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
                  >
                    Submit Expert Answer
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
