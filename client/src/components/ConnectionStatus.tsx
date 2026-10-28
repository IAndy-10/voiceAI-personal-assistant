import type { ConnectionStatus as Status, Speaker } from "../types/conversation";

const STATUS: Record<Status, { label: string; dot: string }> = {
  disconnected: { label: "Disconnected", dot: "bg-zinc-400" },
  connecting: { label: "Connecting", dot: "bg-amber-400 animate-pulse" },
  connected: { label: "Connected", dot: "bg-sky-500 animate-pulse" },
  ready: { label: "Ready", dot: "bg-emerald-500" },
  error: { label: "Error", dot: "bg-red-500" },
};

function speakingLabel(speaker: Speaker): string {
  if (speaker === "user") return "You are speaking";
  if (speaker === "assistant") return "Assistant is speaking";
  return "Listening";
}

interface Props {
  status: Status;
  speaker: Speaker;
}

export function ConnectionStatus({ status, speaker }: Props) {
  const { label, dot } = STATUS[status];
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="flex items-center gap-2 font-medium" role="status">
        <span className={`size-2.5 rounded-full ${dot}`} />
        {label}
      </span>
      {status === "ready" && (
        <span className={speaker ? "text-zinc-900 dark:text-zinc-100" : "text-zinc-500"}>
          {speakingLabel(speaker)}
        </span>
      )}
    </div>
  );
}
