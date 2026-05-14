import { useEffect, useState } from "react";
import { AlertCircle } from "lucide-react";
import { analyzeFile, analyzeSample, getHealth } from "./api";
import type { AnalysisResult, Health } from "./types";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { UploadPanel } from "./components/UploadPanel";
import { ResultsView } from "./components/ResultsView";
import { ChatPanel } from "./components/ChatPanel";

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dark, setDark] = useState<boolean>(() =>
    document.documentElement.classList.contains("dark"),
  );

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((e) =>
        setError(
          `Backend unreachable: ${(e as Error).message}. Is uvicorn running on :8000?`,
        ),
      );
  }, []);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("waferai-theme", next ? "dark" : "light");
  }

  async function runAnalyze(promise: Promise<AnalysisResult>) {
    setLoading(true);
    setError(null);
    try {
      const res = await promise;
      setResult(res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full min-h-screen">
      <Sidebar active="analyze" onChange={() => {}} />

      <div className="flex min-h-screen flex-1 flex-col">
        <TopBar health={health} dark={dark} onToggleTheme={toggleTheme} />

        <main className="flex-1">
          {/* Subtle background pattern */}
          <div className="absolute inset-0 -z-10 bg-grid-light bg-[size:32px_32px] opacity-40 dark:bg-grid-dark" />

          <div className="mx-auto max-w-6xl space-y-6 px-6 py-8 lg:px-8">
            <Hero result={result} loading={loading} />

            {error && (
              <div className="flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300 animate-fade-in">
                <AlertCircle size={18} className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <UploadPanel
              loading={loading}
              onAnalyze={(file) => runAnalyze(analyzeFile(file))}
              onAnalyzeSample={(name) => runAnalyze(analyzeSample(name))}
            />

            {result && <ResultsView result={result} />}

            {result && (
              <ChatPanel
                enabled={health?.claude_configured ?? false}
                defectType={result.defect_type}
              />
            )}

            <footer className="pt-4 text-center text-xs text-ink-400">
              WaferAI · WM-811K · {health?.claude_model ?? "—"} ·{" "}
              <span className="font-mono">v0.2</span>
            </footer>
          </div>
        </main>
      </div>
    </div>
  );
}

function Hero({
  result,
  loading,
}: {
  result: AnalysisResult | null;
  loading: boolean;
}) {
  return (
    <section className="animate-fade-in">
      <p className="label-mono">Wafer defect intelligence</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-ink-900 dark:text-ink-50 sm:text-4xl">
        {loading ? (
          <span className="inline-flex items-center gap-3">
            Running analysis
            <span className="inline-block h-2 w-32 overflow-hidden rounded bg-ink-200 dark:bg-ink-800">
              <span className="block h-full w-1/3 bg-brand-500 shimmer" />
            </span>
          </span>
        ) : result ? (
          <>
            Detected <span className="text-gradient">{result.defect_type}</span>{" "}
            <span className="text-ink-400">
              · {result.confidence.toFixed(1)}%
            </span>
          </>
        ) : (
          <>
            Detect and explain semiconductor defects with{" "}
            <span className="text-gradient">computer vision + Claude</span>
          </>
        )}
      </h1>
      <p className="mt-2 max-w-2xl text-sm text-ink-500">
        Upload a wafer map or pick a real WM-811K sample. The classifier
        identifies the defect pattern; Claude reasons about likely root causes,
        immediate fab actions, and long-term process improvements.
      </p>
    </section>
  );
}
