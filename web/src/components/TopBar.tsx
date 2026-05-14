import { Cpu, Activity, Moon, Sun, CircuitBoard } from "lucide-react";
import type { Health } from "../types";

interface Props {
  health: Health | null;
  dark: boolean;
  onToggleTheme: () => void;
}

export function TopBar({ health, dark, onToggleTheme }: Props) {
  return (
    <header className="sticky top-0 z-30 border-b border-ink-200 bg-white/80 backdrop-blur-md dark:border-ink-800 dark:bg-ink-900/80">
      <div className="flex items-center justify-between gap-4 px-6 py-3 lg:px-8">
        <div className="flex items-center gap-3 lg:hidden">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 text-white">
            <CircuitBoard size={18} />
          </div>
          <span className="text-sm font-semibold tracking-tight text-ink-900 dark:text-ink-50">
            WaferAI
          </span>
        </div>

        <div className="hidden lg:block">
          <h1 className="text-sm font-medium text-ink-500 dark:text-ink-400">
            <span className="text-ink-400 dark:text-ink-500">Workspace</span>
            <span className="mx-2 text-ink-300 dark:text-ink-700">/</span>
            <span className="text-ink-900 dark:text-ink-50">Analyse wafer</span>
          </h1>
        </div>

        <div className="flex items-center gap-2">
          <ClassifierPill
            stub={health?.using_stub_classifier ?? true}
            unknown={!health}
          />
          <LlmPill
            configured={health?.claude_configured ?? false}
            model={health?.claude_model}
            unknown={!health}
          />
          <button
            onClick={onToggleTheme}
            className="btn-ghost ml-1 h-9 w-9 !p-0"
            title={dark ? "Switch to light mode" : "Switch to dark mode"}
          >
            {dark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </div>
    </header>
  );
}

function ClassifierPill({ stub, unknown }: { stub: boolean; unknown: boolean }) {
  if (unknown) {
    return (
      <span className="pill-neutral">
        <Cpu size={12} />
        <span className="hidden sm:inline">Classifier:</span> …
      </span>
    );
  }
  const ok = !stub;
  return (
    <span className={ok ? "pill-ok" : "pill-warn"}>
      <Cpu size={12} />
      <span className="hidden sm:inline">Classifier:</span>{" "}
      {ok ? "Trained CNN" : "Heuristic"}
    </span>
  );
}

function LlmPill({
  configured,
  model,
  unknown,
}: {
  configured: boolean;
  model?: string;
  unknown: boolean;
}) {
  if (unknown) {
    return (
      <span className="pill-neutral">
        <Activity size={12} />
        <span className="hidden sm:inline">LLM:</span> …
      </span>
    );
  }
  return (
    <span className={configured ? "pill-ok" : "pill-warn"}>
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          configured ? "bg-emerald-500 animate-pulse-dot" : "bg-amber-500"
        }`}
      />
      <span className="hidden sm:inline">LLM:</span>{" "}
      <span className="font-mono text-[11px]">{configured ? model : "fallback"}</span>
    </span>
  );
}
