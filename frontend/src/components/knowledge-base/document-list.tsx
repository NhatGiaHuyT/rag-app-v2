"use client";

import { useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { formatDistanceToNow } from "date-fns";
import { api, ApiError } from "@/lib/api";
import { FileIcon, defaultStyles } from "react-file-icon";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { FileText, Lock, Globe, Users, ShieldCheck } from "lucide-react";

interface PermissionAssignment {
  user_id: number;
  username: string;
  full_name?: string | null;
  permission_level: string;
}

interface Document {
  id: number;
  file_name: string;
  file_path: string;
  file_size: number;
  content_type: string;
  created_at: string;
  access_level: string;
  processing_tasks: Array<{
    id: number;
    status: string;
    error_message: string | null;
  }>;
  permissions: PermissionAssignment[];
}

interface KnowledgeBase {
  id: number;
  name: string;
  description: string;
  visibility: string;
  documents: Document[];
  permissions: PermissionAssignment[];
}

interface ShareableUser {
  id: number;
  username: string;
  full_name?: string | null;
}

interface DocumentListProps {
  knowledgeBaseId: number;
}

const visibilityOptions = [
  { value: "private", label: "Private", icon: Lock },
  { value: "public", label: "Public", icon: Globe },
];

const documentAccessOptions = [
  { value: "inherit", label: "Inherit KB" },
  { value: "restricted", label: "Restricted" },
  { value: "public", label: "Public" },
];

export function DocumentList({ knowledgeBaseId }: DocumentListProps) {
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [users, setUsers] = useState<ShareableUser[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [kbViewerIds, setKbViewerIds] = useState<number[]>([]);
  const [kbEditorIds, setKbEditorIds] = useState<number[]>([]);
  const [kbVisibility, setKbVisibility] = useState("private");
  const [docViewerIds, setDocViewerIds] = useState<number[]>([]);
  const [docEditorIds, setDocEditorIds] = useState<number[]>([]);

  const fetchData = async () => {
    try {
      const [kbData, userData] = await Promise.all([
        api.get(`/api/knowledge-base/${knowledgeBaseId}`),
        api.get("/api/auth/users"),
      ]);
      setKnowledgeBase(kbData);
      setUsers(userData);
      setKbVisibility(kbData.visibility);
      setKbViewerIds(
        kbData.permissions
          .filter((permission: PermissionAssignment) => permission.permission_level === "viewer")
          .map((permission: PermissionAssignment) => permission.user_id)
      );
      setKbEditorIds(
        kbData.permissions
          .filter((permission: PermissionAssignment) => permission.permission_level === "editor")
          .map((permission: PermissionAssignment) => permission.user_id)
      );
    } catch (fetchError) {
      if (fetchError instanceof ApiError) {
        setError(fetchError.message);
      } else {
        setError("Failed to fetch documents");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [knowledgeBaseId]);

  const openDocumentShare = (document: Document) => {
    setSelectedDocument(document);
    setDocViewerIds(
      document.permissions
        .filter((permission) => permission.permission_level === "viewer")
        .map((permission) => permission.user_id)
    );
    setDocEditorIds(
      document.permissions
        .filter((permission) => permission.permission_level === "editor")
        .map((permission) => permission.user_id)
    );
  };

  const availableUsers = useMemo(() => users, [users]);

  const toggleUser = (
    userId: number,
    selectedIds: number[],
    setSelectedIds: (value: number[]) => void
  ) => {
    if (selectedIds.includes(userId)) {
      setSelectedIds(selectedIds.filter((id) => id !== userId));
      return;
    }
    setSelectedIds([...selectedIds, userId]);
  };

  const saveKnowledgeBasePermissions = async () => {
    try {
      const data = await api.put(`/api/knowledge-base/${knowledgeBaseId}/permissions`, {
        visibility: kbVisibility,
        user_permissions: kbViewerIds.filter((id) => !kbEditorIds.includes(id)),
        editor_user_ids: kbEditorIds,
      });
      setKnowledgeBase(data);
    } catch (saveError) {
      setError(saveError instanceof ApiError ? saveError.message : "Failed to save permissions");
    }
  };

  const updateDocumentAccess = async (documentId: number, accessLevel: string) => {
    const document = knowledgeBase?.documents.find((item) => item.id === documentId);
    if (!document) {
      return;
    }
    try {
      await api.put(`/api/knowledge-base/${knowledgeBaseId}/documents/${documentId}/permissions`, {
        access_level: accessLevel,
        user_permissions: document.permissions
          .filter((permission) => permission.permission_level === "viewer")
          .map((permission) => permission.user_id),
        editor_user_ids: document.permissions
          .filter((permission) => permission.permission_level === "editor")
          .map((permission) => permission.user_id),
      });
      await fetchData();
    } catch (saveError) {
      setError(saveError instanceof ApiError ? saveError.message : "Failed to update document access");
    }
  };

  const saveDocumentPermissions = async () => {
    if (!selectedDocument) {
      return;
    }
    try {
      await api.put(
        `/api/knowledge-base/${knowledgeBaseId}/documents/${selectedDocument.id}/permissions`,
        {
          access_level: selectedDocument.access_level,
          user_permissions: docViewerIds.filter((id) => !docEditorIds.includes(id)),
          editor_user_ids: docEditorIds,
        }
      );
      setSelectedDocument(null);
      await fetchData();
    } catch (saveError) {
      setError(saveError instanceof ApiError ? saveError.message : "Failed to save document sharing");
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="space-y-4">
          <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto"></div>
          <p className="text-muted-foreground animate-pulse">Loading documents...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-destructive">
          {error}
        </div>
        <button
          type="button"
          onClick={fetchData}
          className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!knowledgeBase) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border bg-card p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <h2 className="text-xl font-semibold">{knowledgeBase.name}</h2>
            <p className="text-sm text-muted-foreground">
              Set who can open this knowledge base and who can edit it.
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-muted px-3 py-2 text-sm">
            {kbVisibility === "public" ? <Globe className="h-4 w-4" /> : <Lock className="h-4 w-4" />}
            {kbVisibility}
          </div>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[220px_1fr_1fr]">
          <div>
            <label className="text-sm font-medium">Knowledge base access</label>
            <select
              value={kbVisibility}
              onChange={(event) => setKbVisibility(event.target.value)}
              className="mt-2 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {visibilityOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <p className="mb-3 flex items-center gap-2 text-sm font-medium">
              <Users className="h-4 w-4" />
              Viewers
            </p>
            <div className="max-h-48 space-y-2 overflow-y-auto rounded-lg border p-3">
              {availableUsers.map((user) => (
                <label key={`viewer-${user.id}`} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={kbViewerIds.includes(user.id)}
                    onChange={() => toggleUser(user.id, kbViewerIds, setKbViewerIds)}
                  />
                  <span>{user.full_name || user.username}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <p className="mb-3 flex items-center gap-2 text-sm font-medium">
              <ShieldCheck className="h-4 w-4" />
              Editors
            </p>
            <div className="max-h-48 space-y-2 overflow-y-auto rounded-lg border p-3">
              {availableUsers.map((user) => (
                <label key={`editor-${user.id}`} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={kbEditorIds.includes(user.id)}
                    onChange={() => toggleUser(user.id, kbEditorIds, setKbEditorIds)}
                  />
                  <span>{user.full_name || user.username}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-4">
          <button
            type="button"
            onClick={saveKnowledgeBasePermissions}
            className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
          >
            Save Knowledge Base Permissions
          </button>
        </div>
      </div>

      {knowledgeBase.documents.length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
          <div className="flex flex-col items-center max-w-[420px] text-center space-y-6">
            <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center">
              <FileText className="w-10 h-10 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-semibold">No documents yet</h3>
              <p className="text-muted-foreground">
                Upload your first document to start building your knowledge base.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Size</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Access</TableHead>
              <TableHead>Sharing</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {knowledgeBase.documents.map((doc) => (
              <TableRow key={doc.id}>
                <TableCell className="font-medium">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6">
                      {doc.content_type.toLowerCase().includes("pdf") ? (
                        <FileIcon extension="pdf" {...defaultStyles.pdf} />
                      ) : doc.content_type.toLowerCase().includes("doc") ? (
                        <FileIcon extension="doc" {...defaultStyles.docx} />
                      ) : doc.content_type.toLowerCase().includes("txt") ? (
                        <FileIcon extension="txt" {...defaultStyles.txt} />
                      ) : doc.content_type.toLowerCase().includes("md") ? (
                        <FileIcon extension="md" {...defaultStyles.md} />
                      ) : (
                        <FileIcon
                          extension={doc.file_name.split(".").pop() || ""}
                          color="#E2E8F0"
                          labelColor="#94A3B8"
                        />
                      )}
                    </div>
                    {doc.file_name}
                  </div>
                </TableCell>
                <TableCell>{(doc.file_size / 1024 / 1024).toFixed(2)} MB</TableCell>
                <TableCell>
                  {formatDistanceToNow(new Date(doc.created_at), {
                    addSuffix: true,
                  })}
                </TableCell>
                <TableCell>
                  {doc.processing_tasks.length > 0 && (
                    <Badge
                      variant={
                        doc.processing_tasks[0].status === "completed"
                          ? "secondary"
                          : doc.processing_tasks[0].status === "failed"
                          ? "destructive"
                          : "default"
                      }
                    >
                      {doc.processing_tasks[0].status}
                    </Badge>
                  )}
                </TableCell>
                <TableCell>
                  <select
                    value={doc.access_level}
                    onChange={(event) => updateDocumentAccess(doc.id, event.target.value)}
                    className="flex h-9 rounded-md border border-input bg-background px-2 text-sm"
                  >
                    {documentAccessOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </TableCell>
                <TableCell>
                  <button
                    type="button"
                    onClick={() => openDocumentShare(doc)}
                    className="inline-flex items-center rounded-md border px-3 py-2 text-sm font-medium hover:bg-accent"
                  >
                    Share
                  </button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <Dialog open={Boolean(selectedDocument)} onOpenChange={(open) => !open && setSelectedDocument(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Share Document</DialogTitle>
          </DialogHeader>
          {selectedDocument && (
            <div className="space-y-6">
              <div>
                <p className="font-medium">{selectedDocument.file_name}</p>
                <p className="text-sm text-muted-foreground">
                  Choose who can view or edit this document.
                </p>
              </div>

              <div>
                <label className="text-sm font-medium">Access level</label>
                <select
                  value={selectedDocument.access_level}
                  onChange={(event) =>
                    setSelectedDocument({
                      ...selectedDocument,
                      access_level: event.target.value,
                    })
                  }
                  className="mt-2 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {documentAccessOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="mb-2 text-sm font-medium">Viewers</p>
                  <div className="max-h-64 space-y-2 overflow-y-auto rounded-lg border p-3">
                    {users.map((user) => (
                      <label key={`doc-viewer-${user.id}`} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={docViewerIds.includes(user.id)}
                          onChange={() => toggleUser(user.id, docViewerIds, setDocViewerIds)}
                        />
                        <span>{user.full_name || user.username}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="mb-2 text-sm font-medium">Editors</p>
                  <div className="max-h-64 space-y-2 overflow-y-auto rounded-lg border p-3">
                    {users.map((user) => (
                      <label key={`doc-editor-${user.id}`} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={docEditorIds.includes(user.id)}
                          onChange={() => toggleUser(user.id, docEditorIds, setDocEditorIds)}
                        />
                        <span>{user.full_name || user.username}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setSelectedDocument(null)}
                  className="rounded-md border px-4 py-2 text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={saveDocumentPermissions}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
                >
                  Save Sharing
                </button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
