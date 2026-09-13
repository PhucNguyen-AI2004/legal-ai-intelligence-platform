import { FilePlus2, Send } from "lucide-react";
import { IconButton } from "@/components/ui/icon-button";

export function ChatComposer() {
  return (
    <div className="composer-wrap">
      <form className="chat-composer">
        <IconButton label="Chọn tài liệu (sắp có)"><FilePlus2 size={20} /></IconButton>
        <label className="sr-only" htmlFor="chat-input">Câu hỏi</label>
        <textarea id="chat-input" rows={1} placeholder="Hỏi Legal AI về tài liệu của bạn…" />
        <IconButton className="send-button" label="Gửi câu hỏi (sắp có)"><Send size={18} /></IconButton>
      </form>
      <p>Legal AI trả lời dựa trên các tài liệu bạn đã chọn.</p>
    </div>
  );
}
