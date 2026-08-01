import {
  Bot,
  Check,
  Clipboard,
  Loader2,
  MessageCircle,
  RotateCcw,
  Send,
  Sparkles,
  Trash2,
  User,
} from "lucide-react";
import {
  useEffect,
  useRef,
  useState,
} from "react";

export type CopilotMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
};

type CopilotChatProps = {
  datasetId: string | null;
  messages: CopilotMessage[];
  isLoading: boolean;
  errorMessage: string | null;
  onSendQuestion: (
    question: string,
  ) => Promise<void>;
  onClearConversation: () => void;
  onRegenerateLastAnswer: () => Promise<void>;
};

const SUGGESTED_QUESTIONS = [
  "Which columns should I clean first?",
  "Why is the reliability score low?",
  "Explain the detected anomalies.",
  "Can I use this dataset for machine learning?",
];

function createMessageId(): string {
  return `${Date.now()}-${Math.random()
    .toString(36)
    .slice(2)}`;
}

export function createCopilotMessage(
  role: CopilotMessage["role"],
  content: string,
): CopilotMessage {
  return {
    id: createMessageId(),
    role,
    content,
    createdAt: new Date().toISOString(),
  };
}

function formatTimestamp(
  timestamp: string,
): string {
  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      hour: "numeric",
      minute: "2-digit",
    },
  ).format(date);
}

export default function CopilotChat({
  datasetId,
  messages,
  isLoading,
  errorMessage,
  onSendQuestion,
  onClearConversation,
  onRegenerateLastAnswer,
}: CopilotChatProps) {
  const [question, setQuestion] =
    useState("");

  const [copiedMessageId, setCopiedMessageId] =
    useState<string | null>(null);

  const messagesEndRef =
    useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, isLoading]);

  async function submitQuestion(
    value: string,
  ): Promise<void> {
    const cleanedQuestion =
      value.trim();

    if (
      !cleanedQuestion ||
      !datasetId ||
      isLoading
    ) {
      return;
    }

    setQuestion("");

    await onSendQuestion(
      cleanedQuestion,
    );
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    await submitQuestion(question);
  }

  function handleKeyDown(
    event: React.KeyboardEvent<HTMLTextAreaElement>,
  ): void {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      void submitQuestion(question);
    }
  }

  async function copyMessage(
    message: CopilotMessage,
  ): Promise<void> {
    try {
      await navigator.clipboard.writeText(
        message.content,
      );

      setCopiedMessageId(
        message.id,
      );

      window.setTimeout(() => {
        setCopiedMessageId(
          (currentId) =>
            currentId === message.id
              ? null
              : currentId,
        );
      }, 1500);
    } catch {
      setCopiedMessageId(null);
    }
  }

  const hasConversation =
    messages.length > 0;

  const canRegenerate =
    datasetId !== null &&
    !isLoading &&
    messages.some(
      (message) =>
        message.role === "user",
    );

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-violet-50 p-2 text-violet-700">
            <MessageCircle size={21} />
          </div>

          <div>
            <p className="text-sm font-medium text-slate-500">
              Interactive intelligence
            </p>

            <h3 className="mt-1 text-lg font-semibold text-slate-950">
              AI Data Copilot
            </h3>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div
            className={[
              "rounded-full px-3 py-1 text-xs font-semibold",
              datasetId
                ? "bg-emerald-50 text-emerald-700"
                : "bg-slate-100 text-slate-500",
            ].join(" ")}
          >
            {datasetId
              ? "Dataset connected"
              : "Upload required"}
          </div>

          <button
            type="button"
            disabled={!canRegenerate}
            onClick={() =>
              void onRegenerateLastAnswer()
            }
            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 transition hover:border-violet-300 hover:text-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RotateCcw size={14} />
            Regenerate
          </button>

          <button
            type="button"
            disabled={
              !hasConversation ||
              isLoading
            }
            onClick={
              onClearConversation
            }
            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 transition hover:border-red-300 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Trash2 size={14} />
            Clear
          </button>
        </div>
      </div>

      <div className="grid min-h-[520px] lg:grid-cols-[0.72fr_1.28fr]">
        <aside className="border-b border-slate-200 bg-slate-50 p-5 lg:border-b-0 lg:border-r">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
            <Sparkles
              size={17}
              className="text-violet-600"
            />
            Suggested questions
          </div>

          <div className="mt-4 space-y-3">
            {SUGGESTED_QUESTIONS.map(
              (suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  disabled={
                    !datasetId ||
                    isLoading
                  }
                  onClick={() =>
                    void submitQuestion(
                      suggestion,
                    )
                  }
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-left text-sm leading-6 text-slate-600 transition hover:border-violet-300 hover:text-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {suggestion}
                </button>
              ),
            )}
          </div>

          <div className="mt-6 rounded-xl border border-blue-100 bg-blue-50 p-4">
            <p className="text-sm font-semibold text-blue-900">
              Privacy-aware context
            </p>

            <p className="mt-2 text-xs leading-5 text-blue-700">
              The copilot receives
              aggregated profile statistics,
              quality findings, rules, and
              recommendations. Raw preview
              records are excluded from the
              prompt.
            </p>
          </div>
        </aside>

        <div className="flex min-h-[520px] flex-col">
          <div className="flex-1 space-y-5 overflow-y-auto p-6">
            {messages.length === 0 ? (
              <div className="flex h-full min-h-72 flex-col items-center justify-center text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-violet-50 text-violet-700">
                  <Bot size={30} />
                </div>

                <h4 className="mt-4 text-lg font-semibold text-slate-950">
                  Ask about your dataset
                </h4>

                <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
                  Ask which columns need
                  attention, why the score is
                  low, whether the data is
                  ready for machine learning,
                  or how to handle anomalies.
                </p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={[
                    "flex gap-3",
                    message.role ===
                    "user"
                      ? "justify-end"
                      : "justify-start",
                  ].join(" ")}
                >
                  {message.role ===
                    "assistant" && (
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-violet-100 text-violet-700">
                      <Bot size={18} />
                    </div>
                  )}

                  <div className="max-w-[82%]">
                    <div
                      className={[
                        "whitespace-pre-line rounded-2xl px-4 py-3 text-sm leading-7",
                        message.role ===
                        "user"
                          ? "rounded-br-md bg-blue-700 text-white"
                          : "rounded-bl-md border border-slate-200 bg-slate-50 text-slate-700",
                      ].join(" ")}
                    >
                      {message.content}
                    </div>

                    <div
                      className={[
                        "mt-1 flex items-center gap-2 text-xs text-slate-400",
                        message.role ===
                        "user"
                          ? "justify-end"
                          : "justify-start",
                      ].join(" ")}
                    >
                      <span>
                        {formatTimestamp(
                          message.createdAt,
                        )}
                      </span>

                      {message.role ===
                        "assistant" && (
                        <button
                          type="button"
                          onClick={() =>
                            void copyMessage(
                              message,
                            )
                          }
                          className="inline-flex items-center gap-1 rounded-md px-2 py-1 transition hover:bg-slate-100 hover:text-slate-600"
                        >
                          {copiedMessageId ===
                          message.id ? (
                            <>
                              <Check
                                size={13}
                              />
                              Copied
                            </>
                          ) : (
                            <>
                              <Clipboard
                                size={13}
                              />
                              Copy
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>

                  {message.role ===
                    "user" && (
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700">
                      <User size={18} />
                    </div>
                  )}
                </div>
              ))
            )}

            {isLoading && (
              <div className="flex gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-violet-100 text-violet-700">
                  <Bot size={18} />
                </div>

                <div className="flex items-center gap-2 rounded-2xl rounded-bl-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                  <Loader2
                    size={17}
                    className="animate-spin"
                  />
                  Analyzing the dataset
                  profile...
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {errorMessage && (
            <div className="mx-6 mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {errorMessage}
            </div>
          )}

          <form
            onSubmit={handleSubmit}
            className="border-t border-slate-200 p-5"
          >
            <div className="flex items-end gap-3 rounded-2xl border border-slate-300 bg-white p-2 shadow-sm focus-within:border-violet-400 focus-within:ring-4 focus-within:ring-violet-100">
              <textarea
                value={question}
                onChange={(event) =>
                  setQuestion(
                    event.target.value,
                  )
                }
                onKeyDown={
                  handleKeyDown
                }
                disabled={
                  !datasetId ||
                  isLoading
                }
                rows={2}
                maxLength={1000}
                placeholder={
                  datasetId
                    ? "Ask SignalForge about this dataset..."
                    : "Upload and analyze a dataset first..."
                }
                className="min-h-12 flex-1 resize-none border-0 bg-transparent px-3 py-2 text-sm leading-6 text-slate-800 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed"
              />

              <button
                type="submit"
                disabled={
                  !datasetId ||
                  isLoading ||
                  !question.trim()
                }
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-violet-700 text-white transition hover:bg-violet-800 disabled:cursor-not-allowed disabled:opacity-50"
                aria-label="Send question"
              >
                {isLoading ? (
                  <Loader2
                    size={18}
                    className="animate-spin"
                  />
                ) : (
                  <Send size={18} />
                )}
              </button>
            </div>

            <div className="mt-2 flex justify-between gap-4 text-xs text-slate-400">
              <span>
                Press Enter to send.
                Shift + Enter adds a new
                line.
              </span>

              <span>
                {question.length}/1000
              </span>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}