"use client";

import { useRef, useState } from "react";
import { Send, Square } from "lucide-react";
import { IconButton } from "@/components/ui/icon-button";
import { SourcePicker } from "./source-picker";
import { messageRequest } from "@/lib/conversations/message-flow";
import type { CreateMessageRequest } from "@/lib/conversations/types";

interface Props {
  disabled?: boolean;
  busy?: boolean;
  editable?: boolean;
  onStop?: () => void;
  value: string;
  onChange: (value: string) => void;
  onSend: (request: CreateMessageRequest) => Promise<boolean>;
}

export function ChatComposer({ disabled = false, busy = false, editable = false, onStop, value, onChange, onSend }: Props) {
  const [selected, setSelected] = useState<string[]>([]);
  const [pickerVersion, setPickerVersion] = useState(0);
  const submitting = useRef(false);
  const locked = disabled || busy;

  async function submit() {
    const content = value.trim();
    if (locked || submitting.current || !content || content.length > 4000) return;
    submitting.current = true;
    const request = messageRequest(content, selected);
    onChange("");
    setSelected([]);
    setPickerVersion((version) => version + 1);
    try {
      // false means no message POST started (for example creation failed).
      // POST failures are reconciled by the provider, never restored blindly here.
      if (!await onSend(request)) onChange(value);
    } finally { submitting.current = false; }
  }

  return <div className="composer-wrap">
    <SourcePicker key={pickerVersion} selected={selected} onChange={setSelected} disabled={locked} />
    <form className="chat-composer" onSubmit={(event) => { event.preventDefault(); void submit(); }}>
      <label className="sr-only" htmlFor="chat-input">Câu hỏi</label>
      <textarea id="chat-input" rows={2} readOnly={locked && !editable} aria-disabled={locked && !editable} value={value} maxLength={4000} onChange={(event) => onChange(event.target.value)} placeholder="Đặt câu hỏi về tài liệu của bạn…" onKeyDown={(event) => {
        if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); void submit(); }
      }} />
      {onStop ? <IconButton type="button" className="send-button stop-button" label="Dừng chờ phản hồi" onClick={onStop}><Square size={16} fill="currentColor" aria-hidden="true" /></IconButton>
        : <IconButton type="submit" className="send-button" label="Gửi câu hỏi" disabled={locked || !value.trim() || value.trim().length > 4000}><Send size={18} aria-hidden="true" /></IconButton>}
    </form>
    <p role="status">{onStop ? "Đang tìm câu trả lời · Có thể dừng chờ phản hồi" : busy ? "Đang đồng bộ lịch sử…" : `${value.length}/4000 · Enter để gửi · Shift+Enter để xuống dòng`}</p>
  </div>;
}
