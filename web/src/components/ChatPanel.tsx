import { useEffect, useRef, useState } from "react";
import { Send, Bot, User, Sparkles, RotateCw } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { streamChat } from "../api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Props {
  enabled: boolean;
  defectType: string;
}

const SUGGESTIONS = [
  "What's the most likely root cause?",
  "Which tool should I inspect first?",
  "How does this affect yield over a 25-wafer lot?",
];

export function ChatPanel({ enabled, defectType }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setMessages([]);
  }, [defectType]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  async function send(text?: string) {
    const content = (text ?? input).trim();
    if (!content || streaming) return;
    setInput("");
    setMessages((m) => [
      ...m,
      { role: "user", content },
      { role: "assistant", content: "" },
    ]);
    setStreaming(true);

    try {
      for await (const chunk of streamChat(content)) {
        setMessages((m) => {
          const next = [...m];
          const last = next[next.length - 1];
          if (last?.role === "assistant") {
            next[next.length - 1] = {
              ...last,
              content: last.content + chunk,
            };
          }
          return next;
        });
      }
    } catch (err) {
      setMessages((m) => {
        const next = [...m];
        const last = next[next.length - 1];
        if (last?.role === "assistant") {
          next[next.length - 1] = {
            ...last,
            content:
              last.content + `\n\n_Connection error: ${(err as Error).message}_`,
          };
        }
        return next;
      });
    } finally {
      setStreaming(false);
    }
  }

  return (
    <section className="card flex flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-ink-200 px-6 py-4 dark:border-ink-800">
        <div className="flex items-center gap-2.5">
          <div className="grid h-7 w-7 place-items-center rounded-md bg-violet-50 text-violet-600 dark:bg-violet-950/40 dark:text-violet-300">
            <Sparkles size={16} />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-ink-900 dark:text-ink-50">
              Ask follow-up questions
            </h2>
            <p className="text-xs text-ink-500">
              Stream answers from {defectType
                ? `Claude about the detected ${defectType} defect`
                : "Claude"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <button
              onClick={() => setMessages([])}
              disabled={streaming}
              className="btn-ghost h-8 px-2 text-xs"
              title="Clear conversation"
            >
              <RotateCw size={12} />
              Reset
            </button>
          )}
          <span className="label-mono">Step 03</span>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 space-y-4 overflow-y-auto px-6 py-5"
        style={{ minHeight: "18rem", maxHeight: "32rem" }}
      >
        {messages.length === 0 ? (
          <div className="grid h-full place-items-center text-center">
            <div className="max-w-md">
              <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-soft">
                <Bot size={20} />
              </div>
              <p className="text-sm font-medium text-ink-700 dark:text-ink-200">
                {enabled
                  ? `Ready to discuss the ${defectType} defect`
                  : "Add your Anthropic API key to .env to enable chat"}
              </p>
              <p className="mt-1 text-xs text-ink-500">
                Pick a quick prompt or write your own
              </p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    disabled={!enabled || streaming}
                    className="rounded-full border border-ink-200 bg-white px-3 py-1.5 text-xs text-ink-600 transition hover:-translate-y-0.5 hover:border-brand-400 hover:bg-brand-50 hover:text-brand-700 disabled:opacity-50 dark:border-ink-700 dark:bg-ink-900 dark:text-ink-300 dark:hover:border-brand-700 dark:hover:bg-brand-950/40"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <Bubble
              key={i}
              message={m}
              streaming={streaming && i === messages.length - 1}
            />
          ))
        )}
      </div>

      <form
        className="border-t border-ink-200 px-6 py-4 dark:border-ink-800"
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              enabled
                ? "Ask about root cause, mitigation, yield impact…"
                : "Configure Claude to enable chat"
            }
            disabled={!enabled || streaming}
            className="flex-1 rounded-lg border border-ink-200 bg-white px-3.5 py-2.5 text-sm placeholder:text-ink-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200 disabled:cursor-not-allowed disabled:bg-ink-50 dark:border-ink-700 dark:bg-ink-900 dark:text-ink-100 dark:placeholder:text-ink-500 dark:focus:ring-brand-900"
          />
          <button
            type="submit"
            className="btn-primary"
            disabled={!enabled || streaming || !input.trim()}
          >
            <Send size={14} />
            Send
          </button>
        </div>
      </form>
    </section>
  );
}

function Bubble({
  message,
  streaming,
}: {
  message: Message;
  streaming: boolean;
}) {
  const isUser = message.role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""} animate-fade-in`}>
      <div
        className={`mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full ${
          isUser
            ? "bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-soft"
            : "bg-ink-100 text-ink-600 dark:bg-ink-800 dark:text-ink-300"
        }`}
      >
        {isUser ? <User size={14} /> : <Bot size={14} />}
      </div>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
          isUser
            ? "rounded-tr-sm bg-brand-500 text-white"
            : "rounded-tl-sm bg-ink-50 text-ink-800 dark:bg-ink-800/70 dark:text-ink-100"
        }`}
      >
        {message.content ? (
          isUser ? (
            <p className="text-sm leading-relaxed">{message.content}</p>
          ) : (
            <div className="prose-chat">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )
        ) : streaming ? (
          <span className="inline-flex gap-1 align-middle">
            <Dot delay="0ms" />
            <Dot delay="150ms" />
            <Dot delay="300ms" />
          </span>
        ) : null}
        {streaming && message.content ? (
          <span className="ml-1 inline-block h-3 w-0.5 animate-pulse-dot bg-ink-400 align-middle" />
        ) : null}
      </div>
    </div>
  );
}

function Dot({ delay }: { delay: string }) {
  return (
    <span
      className="inline-block h-1.5 w-1.5 animate-pulse-dot rounded-full bg-ink-400"
      style={{ animationDelay: delay }}
    />
  );
}
