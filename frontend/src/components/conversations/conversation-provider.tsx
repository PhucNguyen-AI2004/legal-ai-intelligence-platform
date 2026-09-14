"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createConversation, deleteConversation, listConversations, updateConversation } from "@/lib/conversations/conversation-api";
import { conversationErrorMessage } from "@/lib/conversations/conversation-utils";
import type { ConversationSummary } from "@/lib/conversations/types";

const PAGE_SIZE = 20;
type Dialog = { kind: "rename" | "delete"; conversation: ConversationSummary } | null;

interface ConversationContextValue {
  conversations: ConversationSummary[];
  total: number;
  isLoading: boolean;
  isLoadingMore: boolean;
  isCreating: boolean;
  error: string | null;
  feedback: string | null;
  createNew: () => Promise<void>;
  loadMore: () => Promise<void>;
  retry: () => Promise<void>;
  upsert: (conversation: ConversationSummary) => void;
  requestRename: (conversation: ConversationSummary) => void;
  requestDelete: (conversation: ConversationSummary) => void;
}

const ConversationContext = createContext<ConversationContextValue | null>(null);

function newestFirst(items: ConversationSummary[]) {
  return [...items].sort((a, b) => b.updated_at.localeCompare(a.updated_at) || b.id.localeCompare(a.id));
}

export function ConversationProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  const router = useRouter();
  const pathname = usePathname();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [dialog, setDialog] = useState<Dialog>(null);
  const [isMutating, setIsMutating] = useState(false);
  const [dialogError, setDialogError] = useState<string | null>(null);

  const loadFirstPage = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await listConversations(PAGE_SIZE, 0);
      setConversations(response.items);
      setTotal(response.total);
    } catch (caught) {
      setError(conversationErrorMessage(caught, "load"));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { queueMicrotask(() => void loadFirstPage()); }, [loadFirstPage]);

  const upsert = useCallback((conversation: ConversationSummary) => {
    setConversations((current) => newestFirst([conversation, ...current.filter((item) => item.id !== conversation.id)]));
  }, []);

  async function createNew() {
    if (isCreating) return;
    setIsCreating(true);
    setError(null);
    try {
      const created = await createConversation();
      upsert(created);
      setTotal((value) => value + 1);
      setFeedback("Đã tạo cuộc trò chuyện.");
      router.push(`/app/chat/${created.id}`);
    } catch (caught) {
      setError(conversationErrorMessage(caught, "create"));
    } finally {
      setIsCreating(false);
    }
  }

  async function loadMore() {
    if (isLoadingMore || conversations.length >= total) return;
    setIsLoadingMore(true);
    setError(null);
    try {
      const response = await listConversations(PAGE_SIZE, conversations.length);
      setConversations((current) => newestFirst([...current, ...response.items.filter((next) => !current.some((item) => item.id === next.id))]));
      setTotal(response.total);
    } catch (caught) {
      setError(conversationErrorMessage(caught, "load"));
    } finally {
      setIsLoadingMore(false);
    }
  }

  async function submitRename(title: string) {
    if (!dialog || dialog.kind !== "rename") return;
    setIsMutating(true);
    setDialogError(null);
    try {
      const updated = await updateConversation(dialog.conversation.id, title);
      upsert(updated);
      setFeedback("Đã đổi tên cuộc trò chuyện.");
      setDialog(null);
    } catch (caught) {
      setDialogError(conversationErrorMessage(caught, "rename"));
    } finally {
      setIsMutating(false);
    }
  }

  async function confirmDelete() {
    if (!dialog || dialog.kind !== "delete") return;
    const target = dialog.conversation;
    setIsMutating(true);
    setDialogError(null);
    try {
      await deleteConversation(target.id);
      setConversations((current) => current.filter((item) => item.id !== target.id));
      setTotal((value) => Math.max(0, value - 1));
      setFeedback("Đã xóa cuộc trò chuyện.");
      setDialog(null);
      if (pathname === `/app/chat/${target.id}`) router.push("/app/chat");
    } catch (caught) {
      setDialogError(conversationErrorMessage(caught, "delete"));
    } finally {
      setIsMutating(false);
    }
  }

  const value: ConversationContextValue = {
    conversations, total, isLoading, isLoadingMore, isCreating, error, feedback,
    createNew, loadMore, retry: loadFirstPage, upsert,
    requestRename: (conversation) => { setDialog({ kind: "rename", conversation }); setDialogError(null); },
    requestDelete: (conversation) => { setDialog({ kind: "delete", conversation }); setDialogError(null); },
  };

  return <ConversationContext.Provider value={value}>{children}{dialog?.kind === "rename" && <RenameDialog conversation={dialog.conversation} busy={isMutating} error={dialogError} onClose={() => setDialog(null)} onSubmit={(title) => void submitRename(title)} />}{dialog?.kind === "delete" && <DeleteDialog conversation={dialog.conversation} busy={isMutating} error={dialogError} onClose={() => setDialog(null)} onConfirm={() => void confirmDelete()} />}</ConversationContext.Provider>;
}

export function useConversations() {
  const context = useContext(ConversationContext);
  if (!context) throw new Error("useConversations must be used inside ConversationProvider");
  return context;
}

function RenameDialog({ conversation, busy, error, onClose, onSubmit }: { conversation: ConversationSummary; busy: boolean; error: string | null; onClose: () => void; onSubmit: (title: string) => void }) {
  const [title, setTitle] = useState(conversation.title);
  const cleanTitle = title.trim();
  return <div className="dialog-backdrop" role="presentation"><section className="dialog-card" role="dialog" aria-modal="true" aria-labelledby="rename-conversation-title"><h2 id="rename-conversation-title">Đổi tên hội thoại</h2><form onSubmit={(event) => { event.preventDefault(); if (cleanTitle) onSubmit(cleanTitle); }}><Input autoFocus label="Tên hội thoại" value={title} maxLength={255} onChange={(event) => setTitle(event.target.value)} />{error && <p className="form-alert form-error" role="alert">{error}</p>}<div className="dialog-actions"><Button type="button" variant="secondary" onClick={onClose} disabled={busy}>Hủy</Button><Button type="submit" disabled={busy || !cleanTitle}>{busy ? "Đang lưu..." : "Lưu"}</Button></div></form></section></div>;
}

function DeleteDialog({ conversation, busy, error, onClose, onConfirm }: { conversation: ConversationSummary; busy: boolean; error: string | null; onClose: () => void; onConfirm: () => void }) {
  return <div className="dialog-backdrop" role="presentation"><section className="dialog-card" role="alertdialog" aria-modal="true" aria-labelledby="delete-conversation-title"><h2 id="delete-conversation-title">Xóa hội thoại?</h2><p className="dialog-document-name">{conversation.title}</p><p>Toàn bộ lịch sử tin nhắn của hội thoại này sẽ bị xóa. Hành động này không thể hoàn tác.</p>{error && <p className="form-alert form-error" role="alert">{error}</p>}<div className="dialog-actions"><Button autoFocus type="button" variant="secondary" onClick={onClose} disabled={busy}>Hủy</Button><Button type="button" className="button-danger" onClick={onConfirm} disabled={busy}>{busy ? "Đang xóa..." : "Xóa hội thoại"}</Button></div></section></div>;
}
