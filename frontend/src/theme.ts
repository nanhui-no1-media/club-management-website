import { useEffect, useState } from "react";

// 颜色主题：浅色 / 深色 / 跟随系统。偏好存 localStorage（按设备，游客亦可用），
// 并镜像到 Django 后台约定的 `theme` 键（auto/light/dark），使 /admin/ 自动跟随。
export type ThemePreference = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

export const STORAGE_KEY = "cobalt:theme";
// Django admin（4.2+ 自带 data-theme）读取的键，值域 auto|light|dark。
const DJANGO_THEME_KEY = "theme";

export const THEME_OPTIONS: { value: ThemePreference; label: string }[] = [
  { value: "light", label: "浅色模式" },
  { value: "dark", label: "深色模式" },
  { value: "system", label: "跟随系统" },
];

type Listener = (resolved: ResolvedTheme) => void;
const listeners = new Set<Listener>();

function systemDark(): boolean {
  try {
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  } catch {
    return false;
  }
}

export function resolveTheme(pref: ThemePreference): ResolvedTheme {
  return pref === "system" ? (systemDark() ? "dark" : "light") : pref;
}

function mirrorDjango(pref: ThemePreference) {
  try {
    localStorage.setItem(DJANGO_THEME_KEY, pref === "system" ? "auto" : pref);
  } catch {
    /* ignore */
  }
}

function apply(pref: ThemePreference) {
  const resolved = resolveTheme(pref);
  const root = document.documentElement;
  root.dataset.theme = resolved;
  root.style.colorScheme = resolved;
  mirrorDjango(pref);
  listeners.forEach((fn) => fn(resolved));
}

export function getTheme(): ThemePreference {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v === "light" || v === "dark" || v === "system") return v;
  } catch {
    /* ignore */
  }
  return "light";
}

export function setTheme(pref: ThemePreference) {
  try {
    localStorage.setItem(STORAGE_KEY, pref);
  } catch {
    /* ignore */
  }
  apply(pref);
}

export function subscribeTheme(fn: Listener): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

export function initTheme() {
  if (typeof window.matchMedia === "function") {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      if (getTheme() === "system") apply("system");
    };
    if (typeof media.addEventListener === "function") {
      media.addEventListener("change", onChange);
    }
  }
  apply(getTheme());
}

export function useTheme() {
  const [pref, setPrefState] = useState<ThemePreference>(getTheme);
  const [resolved, setResolved] = useState<ResolvedTheme>(() => resolveTheme(getTheme()));

  useEffect(() => {
    return subscribeTheme((res) => {
      setPrefState(getTheme());
      setResolved(res);
    });
  }, []);

  const setPref = (p: ThemePreference) => {
    setTheme(p);
    setPrefState(p);
    setResolved(resolveTheme(p));
  };

  return { pref, resolved, setPref };
}
