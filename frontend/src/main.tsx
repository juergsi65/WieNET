import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

// Lokal gebündelt statt über externe CDNs (Google Fonts, jsdelivr) geladen - eine
// selbstgehostete Anwendung darf beim Erstladen nicht von der Erreichbarkeit
// externer Drittanbieter-Server abhängen (verzögerter/fehlender Seitenaufbau in
// Umgebungen mit eingeschränktem oder gefiltertem Internetzugang, z.B. LXC-Container
// hinter restriktiver Firewall).
import "@fontsource/space-grotesk/500.css";
import "@fontsource/space-grotesk/600.css";
import "@fontsource/space-grotesk/700.css";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/500.css";
import "maplibre-gl/dist/maplibre-gl.css";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
