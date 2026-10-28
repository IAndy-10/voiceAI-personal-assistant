export type Language = "es" | "en";

export const LANGUAGES: { code: Language; label: string }[] = [
  { code: "en", label: "English" },
  { code: "es", label: "Español" },
];

/** The five states shown to the user, collapsed from the SDK's transport states. */
export type ConnectionStatus = "disconnected" | "connecting" | "connected" | "ready" | "error";

export type Speaker = "user" | "assistant" | null;

export interface Message {
  id: string;
  role: "user" | "assistant";
  /** Messages only merge with the previous one from the same session. */
  session: number;
  /** Final text. */
  text: string;
  /** Interim user transcript, replaced once the final text arrives. */
  interim: string;
}
