import { useEffect, useRef, useState } from "react";
import { THEME_OPTIONS, useTheme } from "../theme";
import "./ThemeToggle.css";

function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

export default function ThemeToggle() {
  const { pref, resolved, setPref } = useTheme();
  const [open, setOpen] = useState(false);
  const wrap = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (wrap.current && !wrap.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);

  return (
    <div className="theme-toggle-wrap" ref={wrap}>
      <button
        className="theme-toggle-btn"
        type="button"
        aria-label={resolved === "dark" ? "切换为浅色模式" : "切换为深色模式"}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {resolved === "dark" ? <MoonIcon /> : <SunIcon />}
      </button>
      {open && (
        <div className="theme-menu is-open" role="menu" aria-label="颜色模式">
          {THEME_OPTIONS.map((o) => (
            <button
              key={o.value}
              className={"theme-menu-item" + (pref === o.value ? " is-current" : "")}
              type="button"
              role="menuitemradio"
              aria-checked={pref === o.value}
              onClick={() => {
                setPref(o.value);
                setOpen(false);
              }}
            >
              <span className="theme-dot" aria-hidden="true" />
              {o.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
