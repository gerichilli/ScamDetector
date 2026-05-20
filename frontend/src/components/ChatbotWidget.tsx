import { Bot, BotMessageSquare, Mic, MicOff, Send, Upload, X } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";
import { recognize } from "tesseract.js";

type ChatMessage = {
  id: number;
  role: "assistant" | "user";
  content: string;
  tone?: "danger" | "warning" | "safe";
};

const initialMessages: ChatMessage[] = [
  {
    id: 1,
    role: "assistant",
    content: "Chào bác ạ. Cháu là trợ lý cảnh báo lừa đảo. Bác có thể nhập câu hỏi hoặc tình huống cần kiểm tra.",
  },
  {
    id: 2,
    role: "assistant",
    content: "Nếu có người yêu cầu bác đọc mã OTP, chuyển tiền gấp, hoặc bấm vào link lạ, bác nên dừng lại và hỏi người thân trước ạ.",
  },
];

function getDemoReply(text: string) {
  const normalized = text.toLowerCase();
  if (normalized.includes("otp") || normalized.includes("mã xác thực")) {
    return "NGUY HIỂM: Bác tuyệt đối không đọc mã OTP hoặc mã xác thực cho bất kỳ ai. Nếu đã lỡ đọc, hãy gọi ngân hàng và đổi mật khẩu ngay.";
  }
  if (normalized.includes("chuyển tiền") || normalized.includes("chuyển khoản")) {
    return "CẢNH BÁO: Bác không nên chuyển tiền khi chưa xác minh trực tiếp với người thân, ngân hàng hoặc cơ quan chính thức.";
  }
  if (normalized.includes("link") || normalized.includes("đường dẫn") || normalized.includes("nhấp")) {
    return "ĐÁNG NGHI: Bác không nên bấm vào link lạ. Hãy kiểm tra tên miền, người gửi và hỏi người thân trước khi thao tác.";
  }
  if (normalized.includes("trúng thưởng") || normalized.includes("nhận quà") || normalized.includes("đóng phí")) {
    return "ĐÁNG NGHI: Các yêu cầu đóng phí để nhận quà hoặc trúng thưởng thường là dấu hiệu lừa đảo.";
  }
  return "Cháu chưa thấy dấu hiệu lừa đảo rõ ràng, nhưng bác vẫn nên kiểm tra người gửi, số điện thoại, link và không cung cấp thông tin cá nhân.";
}

function compactText(text: string) {
  return text.replace(/\s+/g, " ").trim();
}

function getMessageTone(text: string): ChatMessage["tone"] {
  const normalized = text.toLowerCase();
  if (normalized.includes("nguy hiểm") || normalized.includes("khẩn cấp")) {
    return "danger";
  }
  if (normalized.includes("cảnh báo") || normalized.includes("đáng nghi")) {
    return "warning";
  }
  return "safe";
}

function normalizeDangerText(text: string, tone: ChatMessage["tone"]) {
  const withoutRedAlert = text.replace(/cảnh báo đỏ\s*:/gi, "NGUY HIỂM:");
  if (tone === "danger" && !withoutRedAlert.toLowerCase().includes("nguy hiểm")) {
    return `NGUY HIỂM: ${withoutRedAlert}`;
  }
  return withoutRedAlert;
}

async function analyzeWithBackend(text: string): Promise<Pick<ChatMessage, "content" | "tone">> {
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"}/chat/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) {
    throw new Error("Analyze API error");
  }

  const data = await response.json();
  const reply = data.recommended_action ?? data.summary;
  if (!reply) {
    throw new Error("Analyze API empty response");
  }
  const tone = data.verdict === "danger" || data.verdict === "warning" || data.verdict === "safe" ? data.verdict : getMessageTone(reply);
  const normalizedReply = normalizeDangerText(reply, tone);
  return {
    content: data.ai_used ? `${normalizedReply}\n\nĐã phân tích bằng AI model.` : normalizedReply,
    tone,
  };
}

type SpeechRecognitionEventLike = {
  results: ArrayLike<ArrayLike<{ transcript: string }>>;
};

interface SpeechRecogAPI {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  start(): void;
  stop(): void;
}

export function ChatbotWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [isReadingImage, setIsReadingImage] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [formError, setFormError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const recognitionRef = useRef<SpeechRecogAPI | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [isOpen, messages]);

  async function sendMessage(text: string) {
    const now = Date.now();
    setMessages((current) => [
      ...current,
      { id: now, role: "user", content: text },
      { id: now + 1, role: "assistant", content: "Đang suy nghĩ..." },
    ]);
    setInput("");

    try {
      const reply = await analyzeWithBackend(text);
      setMessages((current) => [...current.slice(0, -1), { id: now + 2, role: "assistant", ...reply }]);
    } catch {
      const reply = getDemoReply(text);
      setMessages((current) => [...current.slice(0, -1), { id: now + 3, role: "assistant", content: reply, tone: getMessageTone(reply) }]);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const trimmed = input.trim();
    setFormError("");
    if (!trimmed) {
      setFormError("Vui lòng nhập nội dung cần kiểm tra.");
      return;
    }
    if (trimmed.length < 3) {
      setFormError("Nội dung cần tối thiểu 3 ký tự.");
      return;
    }
    if (trimmed.length > 2000) {
      setFormError("Nội dung quá dài, vui lòng rút gọn dưới 2000 ký tự.");
      return;
    }
    await sendMessage(trimmed);
  }

  function toggleVoiceInput() {
    if (isListening) {
      recognitionRef.current?.stop();
      return;
    }

    type SpeechRecogCtor = new () => SpeechRecogAPI;
    const SpeechRecognitionCtor = (
      (window as unknown as Record<string, unknown>)["SpeechRecognition"] ??
      (window as unknown as Record<string, unknown>)["webkitSpeechRecognition"]
    ) as SpeechRecogCtor | undefined;

    if (!SpeechRecognitionCtor) {
      setFormError("Trình duyệt chưa hỗ trợ mic. Vui lòng dùng Chrome hoặc Edge.");
      return;
    }

    setFormError("");
    const recognition = new SpeechRecognitionCtor();
    recognition.lang = "vi-VN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = (e: { error: string }) => {
      setIsListening(false);
      if (e.error !== "aborted") {
        setFormError("Không nhận được âm thanh. Vui lòng thử lại.");
      }
    };
    recognition.onresult = (e: SpeechRecognitionEventLike) => {
      const transcript = e.results[0][0].transcript.trim();
      if (transcript) sendMessage(transcript);
    };

    recognitionRef.current = recognition;
    recognition.start();
  }

  async function handleImageUpload(file: File | null) {
    if (!file) return;
    const now = Date.now();
    setIsReadingImage(true);
    setMessages((current) => [
      ...current,
      { id: now, role: "user", content: `Đã gửi ảnh: ${file.name}` },
      { id: now + 1, role: "assistant", content: "Đang đọc chữ trong ảnh..." },
    ]);

    try {
      const result = await recognize(file, "vie+eng", {
        logger: (message) => {
          if (message.status === "recognizing text") {
            const percent = Math.round(message.progress * 100);
            setMessages((current) => [
              ...current.slice(0, -1),
              { id: now + 1, role: "assistant", content: `Đang đọc chữ trong ảnh... ${percent}%` },
            ]);
          }
        },
      });
      const extractedText = compactText(result.data.text);
      const analysis = extractedText
        ? await analyzeWithBackend(extractedText).catch(() => {
            const reply = getDemoReply(extractedText);
            return { content: reply, tone: getMessageTone(reply) };
          })
        : { content: "", tone: "safe" as const };
      const reply = extractedText
        ? `Cháu đọc được: "${extractedText}"\n\n${analysis.content}`
        : "Cháu chưa đọc được chữ rõ ràng trong ảnh này. Bác thử ảnh nét hơn hoặc nhập nội dung tin nhắn vào ô chat giúp cháu.";

      setMessages((current) => [...current.slice(0, -1), { id: now + 2, role: "assistant", content: reply, tone: analysis.tone }]);
    } catch {
      setMessages((current) => [
        ...current.slice(0, -1),
        {
          id: now + 3,
          role: "assistant",
          content:
            "Cháu chưa đọc được ảnh này. Bác thử ảnh rõ hơn, hoặc nhập nội dung trong ảnh vào ô chat để cháu kiểm tra ngay.",
        },
      ]);
    } finally {
      setIsReadingImage(false);
    }
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

          <div className="chatbot-messages">
            {messages.map((message) => {
              const renderedTone = message.role === "assistant" ? (message.tone ?? getMessageTone(message.content)) : undefined;
              return (
                <div
                  className={`chatbot-message chatbot-message-${message.role} ${renderedTone ? `chatbot-message-${renderedTone}` : ""}`}
                  key={message.id}
                >
                  {message.role === "assistant" && <BotMessageSquare size={20} />}
                  <p>{message.content}</p>
                </div>
              );
            })}
            <div ref={messagesEndRef} aria-hidden="true" />
          </div>

          <div className="chatbot-media-controls">
            <label className="chatbot-upload">
              <input
                type="file"
                accept="image/*"
                disabled={isReadingImage}
                onChange={(e) => {
                  const f = e.target.files?.[0] ?? null;
                  handleImageUpload(f);
                  e.target.value = "";
                }}
              />
              <Upload size={18} />
              <span>{isReadingImage ? "Đang đọc ảnh..." : "Đọc ảnh"}</span>
            </label>
            <button
              type="button"
              className={`chatbot-mic${isListening ? " chatbot-mic-listening" : ""}`}
              onClick={toggleVoiceInput}
              aria-label={isListening ? "Dừng ghi âm" : "Nói chuyện"}
            >
              {isListening ? <MicOff size={18} /> : <Mic size={18} />}
              <span>{isListening ? "Đang nghe..." : "Nói chuyện"}</span>
            </button>
          </div>

          <form className="chatbot-form" onSubmit={submit} noValidate>
            <label className="sr-only" htmlFor="chatbot-input">
              Nhập câu hỏi cho trợ lý
            </label>
            {formError && <div className="chatbot-form-error">{formError}</div>}
            <input
              id="chatbot-input"
              value={input}
              onChange={(event) => {
                setInput(event.target.value);
                setFormError("");
              }}
              placeholder="Bác nhập câu hỏi ở đây..."
              aria-invalid={!!formError}
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
            <span className="chatbot-fab-icon" aria-hidden="true">
              <Bot size={30} />
            </span>
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
