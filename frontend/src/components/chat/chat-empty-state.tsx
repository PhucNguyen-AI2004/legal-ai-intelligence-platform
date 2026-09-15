import { BookOpenCheck } from "lucide-react";

export function ChatEmptyState() {
  return (
    <section className="chat-empty" aria-labelledby="chat-empty-title">
      <span className="empty-icon"><BookOpenCheck size={25} /></span>
      <h1 id="chat-empty-title">Tôi có thể giúp bạn tra cứu điều gì?</h1>
      <p>Đặt câu hỏi về tài liệu đã lập chỉ mục. Bạn có thể chọn nguồn riêng cho từng câu hỏi; trích dẫn sẽ hiển thị khi có bằng chứng phù hợp.</p>
    </section>
  );
}
