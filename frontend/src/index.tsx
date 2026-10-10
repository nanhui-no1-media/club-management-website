import { createRoot } from "react-dom/client";
import "./styles/cobalt.css";
import "./styles/theme-dark.css";
import { initTheme } from "./theme";
import App from "./App";

initTheme();
createRoot(document.getElementById("root")!).render(<App />);
