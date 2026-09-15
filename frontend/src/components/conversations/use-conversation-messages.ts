"use client";

import { useCallback, useRef, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { getConversation, sendMessage } from "@/lib/conversations/conversation-api";
import { messagePersistence, type Persistence } from "@/lib/conversations/message-flow";
import type { ConversationDetail, ConversationSummary, CreateMessageRequest } from "@/lib/conversations/types";

export interface Submission {
  request: CreateMessageRequest;
  previousIds: string[];
  phase: "queued" | "sending" | "reconciling" | "settled";
  persistence: Persistence;
  postError: string | null;
  syncError: boolean;
  definitiveFailure: boolean;
  acknowledged: boolean;
}

// Mounted once in ConversationProvider: requests and recovery survive route changes.
// These are keyed resources, not an active-conversation store; the URL selects them.
export function useConversationMessages(upsert: (conversation: ConversationSummary) => void) {
  const [histories, setHistories] = useState<Record<string, ConversationDetail>>({});
  const [submissions, setSubmissions] = useState<Record<string, Submission>>({});
  const historyRef = useRef<Record<string, ConversationDetail>>({});
  const submissionRef = useRef<Record<string, Submission>>({});
  const versions = useRef<Record<string, number>>({});
  const refreshing = useRef(new Map<string, Promise<void>>());

  const saveHistory = useCallback((history: ConversationDetail) => {
    historyRef.current[history.id] = history;
    setHistories((current) => ({ ...current, [history.id]: history }));
    upsert(history);
  }, [upsert]);

  const saveSubmission = useCallback((id: string, submission: Submission) => {
    submissionRef.current[id] = submission;
    setSubmissions((current) => ({ ...current, [id]: submission }));
  }, []);

  const readHistory = useCallback(async (id: string) => {
    const version = (versions.current[id] ?? 0) + 1;
    versions.current[id] = version;
    const history = await getConversation(id);
    if (versions.current[id] === version) saveHistory(history);
    return history;
  }, [saveHistory]);

  const reconcile = useCallback(async (id: string, submission: Submission) => {
    try {
      const history = await readHistory(id);
      saveSubmission(id, {
        ...submission, phase: "settled", syncError: false,
        persistence: submission.postError ? messagePersistence(history, submission.previousIds, submission.request.content, submission.definitiveFailure) : "saved",
      });
    } catch {
      saveSubmission(id, { ...submission, phase: "settled", syncError: true });
    }
  }, [readHistory, saveSubmission]);

  const isSending = useCallback((id: string) => {
    const submission = submissionRef.current[id];
    return refreshing.current.has(id) || Boolean(submission && submission.phase !== "settled");
  }, []);

  const loadHistory = useCallback(async (id: string) => {
    // Share the actual promise: Strict Mode/remount callers must also observe
    // errors, rather than treating an already-running read as a successful read.
    const existing = refreshing.current.get(id);
    if (existing) return existing;
    if (isSending(id)) return;
    const refresh = (async () => {
      const submission = submissionRef.current[id];
      if (submission && (submission.postError || submission.syncError) && !submission.acknowledged) await reconcile(id, submission);
      else await readHistory(id);
    })();
    refreshing.current.set(id, refresh);
    try { await refresh; } finally { refreshing.current.delete(id); }
  }, [isSending, readHistory, reconcile]);

  const queueMessage = useCallback((history: ConversationDetail, request: CreateMessageRequest) => {
    saveHistory(history);
    saveSubmission(history.id, { request, previousIds: history.messages.map((message) => message.id), phase: "queued", persistence: "unknown", postError: null, syncError: false, definitiveFailure: false, acknowledged: false });
  }, [saveHistory, saveSubmission]);

  const submitMessage = useCallback(async (id: string, request?: CreateMessageRequest): Promise<boolean> => {
    const previous = submissionRef.current[id];
    const queued = !request && previous?.phase === "queued";
    if (!queued && (isSending(id) || (previous && !previous.acknowledged && (previous.postError || previous.syncError)))) return false;
    const history = historyRef.current[id];
    const body = queued ? previous.request : request;
    if (!history || !body) return false;
    versions.current[id] = (versions.current[id] ?? 0) + 1;
    let submission: Submission = {
      request: body, previousIds: history.messages.map((message) => message.id), phase: "sending", persistence: "unknown",
      postError: null, syncError: false, definitiveFailure: false, acknowledged: false,
    };
    // Synchronous ref claim prevents duplicate events and Strict Mode replays.
    saveSubmission(id, submission);
    try {
      await sendMessage(id, body);
    } catch (caught) {
      submission = { ...submission,
        definitiveFailure: caught instanceof ApiError && ![408, 502, 504].includes(caught.status),
        postError: caught instanceof ApiError && caught.status === 404
          ? "Không tìm thấy hội thoại hoặc tài liệu đã chọn."
          : "Chưa nhận được phản hồi hoàn chỉnh. Không tự động gửi lại câu hỏi.",
      };
    }
    submission = { ...submission, phase: "reconciling" };
    saveSubmission(id, submission);
    await reconcile(id, submission);
    return true;
  }, [isSending, reconcile, saveSubmission]);

  const acknowledge = useCallback((id: string) => {
    const submission = submissionRef.current[id];
    if (submission?.phase === "settled" && !submission.syncError) saveSubmission(id, { ...submission, acknowledged: true });
  }, [saveSubmission]);

  const forget = useCallback((id: string) => {
    delete historyRef.current[id];
    delete submissionRef.current[id];
    versions.current[id] = (versions.current[id] ?? 0) + 1;
    setHistories((current) => { const next = { ...current }; delete next[id]; return next; });
    setSubmissions((current) => { const next = { ...current }; delete next[id]; return next; });
  }, []);

  return { histories, submissions, loadHistory, queueMessage, submitMessage, acknowledge, isSending, forget };
}
