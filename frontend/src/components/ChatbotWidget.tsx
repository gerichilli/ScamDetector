import { BotMessageSquare, MessageCircle, Send, X } from "lucide-react";
import { FormEvent, useState } from "react";

type ChatMessage = {
  id: number;
  role: "assistant" | "user";
  content: string;
};

const initialMessages: ChatMessage[] = [
  {
    id: 1,
    role: "assistant",
    content: "Chào bác ạ. Cháu là trợ lý cảnh báo lừa đảo. Bác có thể nhập câu hỏi, đội API sẽ kết nối phần trả lời realtime sau.",
  },
  {
    id: 2,
    role: "assistant",
    content: "Nếu có người yêu cầu bác đọc mã OTP, chuyển tiền gấp, hoặc bấm vào link lạ, bác nên dừng lại và hỏi người thân trước ạ.",
  },
];

export function ChatbotWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);

  function submit(event: FormEvent) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;

    setMessages((current) => [
      ...current,
      { id: Date.now(), role: "user", content: trimmed },
      {
        id: Date.now() + 1,
        role: "assistant",
        content: "Cháu đã ghi nhận câu hỏi của bác. Phần trả lời realtime sẽ hoạt động khi API chatbot được kết nối ạ.",
      },
    ]);
    setInput("");
  }

  return (
    <div className="chatbot-widget">
      {isOpen && (
        <section className="chatbot-panel" aria-label="Trợ lý trò chuyện">
          <header className="chatbot-header">
            <div>
              <span className="chatbot-kicker">Trợ lý realtime</span>
              <h2>Hỏi về lừa đảo</h2>
            </div>
            <button className="chatbot-close" type="button" onClick={() => setIsOpen(false)} aria-label="Đóng khung chat">
              <X size={22} />
            </button>
          </header>

          <div className="chatbot-api-note">
            Giao diện đã sẵn sàng. Phần API trả lời realtime sẽ được kết nối sau.
          </div>

          <div className="chatbot-messages">
            {messages.map((message) => (
              <div className={`chatbot-message chatbot-message-${message.role}`} key={message.id}>
                {message.role === "assistant" && <BotMessageSquare size={20} />}
                <p>{message.content}</p>
              </div>
            ))}
          </div>

          <form className="chatbot-form" onSubmit={submit}>
            <label className="sr-only" htmlFor="chatbot-input">Nhập câu hỏi cho trợ lý</label>
            <input
              id="chatbot-input"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Bác nhập câu hỏi ở đây..."
            />
            <button type="submit" aria-label="Gửi câu hỏi">
              <Send size={22} />
            </button>
          </form>
        </section>
      )}

      <button
        className="chatbot-fab"
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        aria-label={isOpen ? "Đóng trợ lý chat" : "Mở trợ lý chat"}
      >
        {isOpen ? (
          <X size={30} />
        ) : (
          <>
            <span className="chatbot-fab-pulse" aria-hidden="true" />
            <MessageCircle size={32} />
            <span>
              <strong>Hỏi trợ lý</strong>
              <small>Cần giúp về lừa đảo?</small>
            </span>
          </>
        )}
      </button>
    </div>
  );
}
