import {
  type BotOutputData,
  type DeviceError,
  type ErrorData,
  type RTVIMessage,
  RTVIEvent,
  TextType,
  type TransportState,
  type UserInputData,
} from "@pipecat-ai/client-js";
import {
  usePipecatClient,
  usePipecatClientTransportState,
  useRTVIClientEvent,
} from "@pipecat-ai/client-react";
import { useCallback, useEffect, useRef, useState } from "react";
import type { ConnectionStatus, Language, Message, Speaker } from "../types/conversation";

const START_ENDPOINT = "/api/start";

function joinText(a: string, b: string): string {
  return `${a} ${b}`.replace(/\s+/g, " ").trim();
}

function toStatus(state: TransportState, failed: boolean): ConnectionStatus {
  switch (state) {
    case "error":
      return "error";
    case "disconnected":
    case "disconnecting":
      return failed ? "error" : "disconnected";
    case "connected":
      return "connected";
    case "ready":
      return "ready";
    default:
      return "connecting";
  }
}

function micErrorMessage(error: DeviceError): string {
  switch (error.type) {
    case "permissions":
      return "Microphone access was denied. Allow it from the site settings in the address bar, then start again.";
    case "not-found":
      return "No microphone was found. Connect one and start again.";
    case "in-use":
      return "The microphone is in use by another app.";
    default:
      return `Microphone error: ${error.message}`;
  }
}

/** Session state and actions for one voice conversation at a time. */
export function useVoiceSession() {
  const client = usePipecatClient();
  const transportState = usePipecatClientTransportState();
  const [messages, setMessages] = useState<Message[]>([]);
  const [speaker, setSpeaker] = useState<Speaker>(null);
  const [error, setError] = useState<string | null>(null);
  const [micError, setMicError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  // Tells a user-initiated End apart from the bot ending the session.
  const endedByUser = useRef(false);
  // Each spoken sentence can produce several bot-output events; show it once.
  const shownSegments = useRef(new Set<number>());
  const session = useRef(0);

  useRTVIClientEvent(
    RTVIEvent.UserInput,
    useCallback((data: UserInputData) => {
      const current = session.current;
      setMessages((prev) => {
        const last = prev.at(-1);
        if (last?.role === "user" && last.session === current) {
          const updated = data.final
            ? { ...last, text: joinText(last.text, data.text), interim: "" }
            : { ...last, interim: data.text };
          return [...prev.slice(0, -1), updated];
        }
        const message: Message = {
          id: crypto.randomUUID(),
          role: "user",
          session: current,
          text: data.final ? data.text : "",
          interim: data.final ? "" : data.text,
        };
        return [...prev, message];
      });
    }, []),
  );

  useRTVIClientEvent(
    RTVIEvent.BotOutput,
    useCallback((data: BotOutputData) => {
      if (data.text_type === TextType.BACKCHANNEL) return;
      if (data.segment_id !== undefined) {
        if (shownSegments.current.has(data.segment_id)) return;
        shownSegments.current.add(data.segment_id);
      }
      const current = session.current;
      setMessages((prev) => {
        const last = prev.at(-1);
        if (last?.role === "assistant" && last.session === current) {
          return [...prev.slice(0, -1), { ...last, text: joinText(last.text, data.text) }];
        }
        const message: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          session: current,
          text: data.text,
          interim: "",
        };
        return [...prev, message];
      });
    }, []),
  );

  useRTVIClientEvent(
    RTVIEvent.UserStartedSpeaking,
    useCallback(() => setSpeaker("user"), []),
  );
  useRTVIClientEvent(
    RTVIEvent.UserStoppedSpeaking,
    useCallback(() => setSpeaker((s) => (s === "user" ? null : s)), []),
  );
  useRTVIClientEvent(
    RTVIEvent.BotStartedSpeaking,
    useCallback(() => setSpeaker("assistant"), []),
  );
  useRTVIClientEvent(
    RTVIEvent.BotStoppedSpeaking,
    useCallback(() => setSpeaker((s) => (s === "assistant" ? null : s)), []),
  );

  useRTVIClientEvent(
    RTVIEvent.Error,
    useCallback((message: RTVIMessage) => {
      const data = message.data as ErrorData;
      setError(data.error ?? data.message ?? "Unknown error");
    }, []),
  );
  useRTVIClientEvent(
    RTVIEvent.DeviceError,
    useCallback((error: DeviceError) => setMicError(micErrorMessage(error)), []),
  );

  useRTVIClientEvent(
    RTVIEvent.BotDisconnected,
    useCallback(() => {
      if (!endedByUser.current) {
        setNotice("The assistant ended the session (no speech for a while, time limit, or a server error).");
      }
    }, []),
  );

  useRTVIClientEvent(
    RTVIEvent.Disconnected,
    useCallback(() => {
      setSpeaker(null);
      shownSegments.current.clear();
    }, []),
  );

  // Release the microphone and connection if the app unmounts mid-session.
  useEffect(() => {
    return () => {
      client?.disconnect().catch(() => {});
    };
  }, [client]);

  const start = useCallback(
    async (language: Language) => {
      if (!client) return;
      session.current += 1;
      endedByUser.current = false;
      setError(null);
      setMicError(null);
      setNotice(null);
      try {
        await client.startBotAndConnect({
          endpoint: START_ENDPOINT,
          requestData: { body: { language } },
        });
      } catch (e) {
        console.error("Failed to start session", e);
        setError("Could not reach the voice bot. Is it running on port 7860 (uv run bot.py)?");
        await client.disconnect().catch(() => {});
      }
    },
    [client],
  );

  const end = useCallback(async () => {
    endedByUser.current = true;
    await client?.disconnect();
  }, [client]);

  const clearTranscript = useCallback(() => setMessages([]), []);

  return {
    status: toStatus(transportState, error !== null),
    speaker,
    messages,
    error,
    micError,
    notice,
    start,
    end,
    clearTranscript,
  };
}
