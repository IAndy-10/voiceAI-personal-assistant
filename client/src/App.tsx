import { useState } from "react";
import { ConnectionStatus } from "./components/ConnectionStatus";
import { LanguagePicker } from "./components/LanguagePicker";
import { Transcript } from "./components/Transcript";
import { VoiceControls } from "./components/VoiceControls";
import { useVoiceSession } from "./hooks/useVoiceSession";
import type { Language } from "./types/conversation";

export default function App() {
  const [language, setLanguage] = useState<Language>("es");
  const session = useVoiceSession();
  const idle = session.status === "disconnected" || session.status === "error";

  return (
    <main className="mx-auto flex h-dvh max-w-xl flex-col gap-4 px-4 py-6">
      <header className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Voice Lab</h1>
        <LanguagePicker value={language} onChange={setLanguage} disabled={!idle} />
      </header>

      <ConnectionStatus status={session.status} speaker={session.speaker} />

      {session.micError && (
        <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:bg-amber-950 dark:text-amber-200">
          {session.micError}
        </p>
      )}
      {session.error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-900 dark:bg-red-950 dark:text-red-200">
          {session.error}
        </p>
      )}

      <VoiceControls
        status={session.status}
        onStart={() => session.start(language)}
        onEnd={session.end}
      />

      <Transcript messages={session.messages} onClear={session.clearTranscript} />
    </main>
  );
}
