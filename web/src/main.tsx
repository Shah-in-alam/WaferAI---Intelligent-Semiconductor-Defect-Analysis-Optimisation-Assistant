import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

// Apply theme before first paint to avoid flash-of-unstyled-content.
const saved = localStorage.getItem("waferai-theme");
const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
const isDark = saved ? saved === "dark" : prefersDark;
document.documentElement.classList.toggle("dark", isDark);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
