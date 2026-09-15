"use client";

import { useRef, useState } from "react";
import { Send } from "lucide-react";
import { IconButton } from "@/components/ui/icon-button";
import { SourcePicker } from "./source-picker";
import { messageRequest } from "@/lib/conversations/message-flow";
import type { CreateMessageRequest } from "@/lib/conversations/types";

interface Props {
  disabled?: boolean;
  busy?: boolean;
  value: string;
  onChange: (value: string) => void;
  onSend: (request: CreateMessageRequest) => Promise<boolean>;
}

export function ChatComposer({ disabled = false, busy = false, value, onChange, onSend }: Props) {
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
      <textarea id="chat-input" rows={2} readOnly={locked} aria-disabled={locked} value={value} maxLength={4000} onChange={(event) => onChange(event.target.value)} placeholder="Đặt câu hỏi về tài liệu của bạn…" onKeyDown={(event) => {
        if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); void submit(); }
      }} />
      <IconButton type="submit" className="send-button" label="Gửi câu hỏi" disabled={locked || !value.trim() || value.trim().length > 4000}><Send size={18} /></IconButton>
    </form>
    <p>{busy ? "Đang gửi và tìm nguồn cho câu trả lời…" : `${value.length}/4000 · Enter để gửi · Shift+Enter để xuống dòng`}</p>
  </div>;
}
