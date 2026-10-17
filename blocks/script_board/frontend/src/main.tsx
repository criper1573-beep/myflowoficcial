import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource/inter-tight/500.css";
import "@fontsource/inter-tight/600.css";
import "@fontsource/onest/400.css";
import "@fontsource/onest/500.css";
import "@fontsource/onest/600.css";
import "@xyflow/react/dist/style.css";
import App from "./App";
import "./App.css";

const root = document.getElementById("root");
if (!root) throw new Error("Нет корневого элемента");

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
