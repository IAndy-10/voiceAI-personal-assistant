import type { ConnectionStatus } from "../types/conversation";

interface Props {
  status: ConnectionStatus;
  onStart: () => void;
  onEnd: () => void;
}

const button =
  "w-full rounded-lg px-4 py-2.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50";

export function VoiceControls({ status, onStart, onEnd }: Props) {
  if (status === "disconnected" || status === "error") {
    return (
      <button
        type="button"
        onClick={onStart}
        className={`${button} bg-zinc-900 text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300`}
      >
        {status === "error" ? "Retry" : "Start conversation"}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onEnd}
      disabled={status === "connecting"}
      className={`${button} border border-zinc-300 hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800`}
    >
      {status === "connecting" ? "Connecting…" : "End conversation"}
    </button>
  );
}
