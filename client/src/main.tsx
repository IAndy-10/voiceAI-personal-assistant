import { PipecatClient } from "@pipecat-ai/client-js";
import { PipecatClientAudio, PipecatClientProvider } from "@pipecat-ai/client-react";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

const client = new PipecatClient({
  transport: new SmallWebRTCTransport(),
  enableMic: true,
  enableCam: false,
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <PipecatClientProvider client={client}>
      <App />
      <PipecatClientAudio />
    </PipecatClientProvider>
  </StrictMode>,
);
