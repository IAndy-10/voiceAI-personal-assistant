import { useEffect, useRef } from "react";
import type { Message } from "../types/conversation";

interface Props {
  messages: Message[];
  onClear: () => void;
}

export function Transcript({ messages, onClear }: Props) {
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  return (
    <section className="flex min-h-0 flex-1 flex-col rounded-xl border border-zinc-200 dark:border-zinc-800">
      <header className="flex items-center justify-between border-b border-zinc-200 px-4 py-2 dark:border-zinc-800">
        <h2 className="text-sm font-medium">Transcript</h2>
        <button
          type="button"
          onClick={onClear}
          disabled={messages.length === 0}
          className="text-xs text-zinc-500 hover:text-zinc-900 disabled:opacity-40 dark:hover:text-zinc-100"
        >
          Clear
        </button>
      </header>
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-center text-sm text-zinc-500">The conversation will appear here.</p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <p
              className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-sm ${
                m.role === "user"
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "bg-zinc-100 dark:bg-zinc-800"
              }`}
            >
              {m.text}
              {m.interim && <span className="opacity-60"> {m.interim}</span>}
            </p>
          </div>
        ))}
        <div ref={end} />
      </div>
    </section>
  );
}
