"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/layout/dashboard-layout";
import { api, ApiError } from "@/lib/api";

interface Profile {
  email: string;
  username: string;
  full_name?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
  is_superuser: boolean;
  is_expert: boolean;
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/api/auth/me")
      .then(setProfile)
      .catch((fetchError) =>
        setError(fetchError instanceof ApiError ? fetchError.message : "Failed to load profile")
      );
  }, []);

  const updateField = (field: keyof Profile, value: string) => {
    if (!profile) {
      return;
    }
    setProfile({ ...profile, [field]: value });
  };

  const handleSave = async () => {
    if (!profile) {
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const data = await api.put("/api/auth/me", profile);
      setProfile(data);
      setMessage("Profile updated successfully.");
    } catch (saveError) {
      setError(saveError instanceof ApiError ? saveError.message : "Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Profile</h1>
          <p className="text-muted-foreground">
            Update your identity, contact information, and reviewer metadata.
          </p>
        </div>

        {error && <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-destructive">{error}</div>}
        {message && <div className="rounded-lg border border-emerald-300 bg-emerald-50 p-4 text-emerald-700">{message}</div>}

        {profile && (
          <div className="rounded-2xl border bg-card p-6 space-y-5">
            <div className="grid gap-5 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium">Full name</label>
                <input
                  value={profile.full_name || ""}
                  onChange={(event) => updateField("full_name", event.target.value)}
                  className="mt-2 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Username</label>
                <input
                  value={profile.username}
                  onChange={(event) => updateField("username", event.target.value)}
                  className="mt-2 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Email</label>
                <input
                  value={profile.email}
                  onChange={(event) => updateField("email", event.target.value)}
                  className="mt-2 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Avatar URL</label>
                <input
                  value={profile.avatar_url || ""}
                  onChange={(event) => updateField("avatar_url", event.target.value)}
                  className="mt-2 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div>
              <label className="text-sm font-medium">Bio</label>
              <textarea
                value={profile.bio || ""}
                onChange={(event) => updateField("bio", event.target.value)}
                rows={5}
                className="mt-2 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>

            <div className="rounded-xl bg-muted/60 p-4 text-sm text-muted-foreground">
              {profile.is_superuser
                ? "You have administrator access."
                : profile.is_expert
                ? "You can review and override assistant answers as an expert."
                : "You have standard user access."}
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleSave}
                disabled={saving}
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-60"
              >
                {saving ? "Saving..." : "Save Profile"}
              </button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
