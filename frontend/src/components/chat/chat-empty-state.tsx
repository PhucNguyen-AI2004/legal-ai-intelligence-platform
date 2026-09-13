import { BookOpenCheck } from "lucide-react";
import { MOCK_SUGGESTED_PROMPTS } from "@/lib/constants/mock-ui";

export function ChatEmptyState() {
  return (
    <section className="chat-empty" aria-labelledby="chat-empty-title">
      <span className="empty-icon"><BookOpenCheck size={25} /></span>
      <h1 id="chat-empty-title">Tôi có thể giúp bạn tra cứu điều gì?</h1>
      <p>Chọn tài liệu và đặt câu hỏi. Câu trả lời sẽ kèm nguồn trích dẫn.</p>
      <div className="prompt-grid" aria-label="Câu hỏi gợi ý">
        {MOCK_SUGGESTED_PROMPTS.map((prompt) => <button key={prompt}>{prompt}</button>)}
      </div>
    </section>
  );
}
