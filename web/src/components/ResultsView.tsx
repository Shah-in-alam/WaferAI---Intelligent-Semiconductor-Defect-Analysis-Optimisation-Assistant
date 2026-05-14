import { useEffect, useMemo } from "react";
import { Download, AlertTriangle, ShieldCheck, Target, BarChart3, Wrench } from "lucide-react";
import { pdfBlobUrl } from "../api";
import type { AnalysisResult } from "../types";

interface Props {
  result: AnalysisResult;
}

const SEVERITY_PILL: Record<string, string> = {
  Low: "pill-ok",
  Medium: "pill-warn",
  High: "pill-warn",
  Critical: "pill-danger",
};

export function ResultsView({ result }: Props) {
  const {
    defect_type,
    confidence,
    probabilities,
    metadata,
    analysis,
    overlay_png_b64,
    pdf_b64,
  } = result;
  const sorted = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);
  const severityClass = SEVERITY_PILL[analysis.severity] ?? "pill-warn";
  const isLow = analysis.severity === "Low";

  // Build a transient blob: URL for the PDF. Revoked when this result is
  // replaced so the browser releases the memory.
  const pdfUrl = useMemo(() => pdfBlobUrl(pdf_b64), [pdf_b64]);
  useEffect(() => () => URL.revokeObjectURL(pdfUrl), [pdfUrl]);

  return (
    <section className="space-y-6 animate-fade-in">
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between border-b border-ink-200 px-6 py-4 dark:border-ink-800">
          <div className="flex items-center gap-2.5">
            <div className="grid h-7 w-7 place-items-center rounded-md bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-300">
              <Target size={16} />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-ink-900 dark:text-ink-50">
                Analysis results
              </h2>
              <p className="text-xs text-ink-500">
                Classification + AI engineering recommendations
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="label-mono">Step 02</span>
            <a
              className="btn-secondary"
              href={pdfUrl}
              download="wafer_report.pdf"
            >
              <Download size={14} />
              PDF
            </a>
          </div>
        </div>

        <div className="grid gap-px bg-ink-200 lg:grid-cols-5 dark:bg-ink-800">
          {/* Prediction summary */}
          <div className="bg-white p-6 dark:bg-ink-900 lg:col-span-2">
            <p className="label-mono">Predicted defect</p>
            <h3 className="mt-2 text-4xl font-semibold tracking-tight text-gradient">
              {defect_type}
            </h3>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="font-mono text-3xl text-ink-900 dark:text-ink-50">
                {confidence.toFixed(1)}
              </span>
              <span className="text-sm text-ink-500">% confidence</span>
            </div>
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-ink-100 dark:bg-ink-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-300 transition-all"
                style={{ width: `${confidence}%` }}
              />
            </div>

            <div className="mt-5">
              <span className={severityClass}>
                {isLow ? <ShieldCheck size={12} /> : <AlertTriangle size={12} />}
                {analysis.severity} severity · {analysis.estimated_yield_loss} yield loss
              </span>
            </div>

            <dl className="mt-6 grid grid-cols-2 gap-3 text-sm">
              <Stat label="Location" value={metadata.location} />
              <Stat label="Density" value={`${metadata.defect_density}%`} />
              <Stat label="Image" value={`${metadata.width}×${metadata.height}`} />
              <Stat label="Top-2 gap" value={`${(sorted[0][1] - sorted[1][1]).toFixed(1)}%`} />
            </dl>
          </div>

          {/* Grad-CAM overlay */}
          <div className="bg-white p-6 dark:bg-ink-900 lg:col-span-3">
            <div className="flex items-center justify-between">
              <p className="label-mono">Model attention · Grad-CAM</p>
            </div>
            <div className="mt-3 overflow-hidden rounded-xl border border-ink-200 bg-gradient-to-br from-ink-50 to-white p-2 dark:border-ink-800 dark:from-ink-950 dark:to-ink-900">
              <img
                src={`data:image/png;base64,${overlay_png_b64}`}
                alt="Grad-CAM overlay"
                className="mx-auto block max-h-80 rounded-lg object-contain"
              />
            </div>
            <p className="mt-2 text-xs text-ink-500">
              Warmer regions = where the model focused when making the prediction.
            </p>
          </div>
        </div>
      </div>

      {/* Confidence chart */}
      <div className="card p-6">
        <div className="flex items-center gap-2.5">
          <div className="grid h-7 w-7 place-items-center rounded-md bg-brand-50 text-brand-600 dark:bg-brand-950/40 dark:text-brand-300">
            <BarChart3 size={16} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-ink-900 dark:text-ink-50">
              Class confidence
            </h3>
            <p className="text-xs text-ink-500">
              Softmax across all 9 WM-811K defect classes
            </p>
          </div>
        </div>
        <div className="mt-5 space-y-2">
          {sorted.map(([name, value], idx) => (
            <div key={name} className="flex items-center gap-3">
              <span className="w-24 shrink-0 font-mono text-xs uppercase tracking-wide text-ink-500">
                {name}
              </span>
              <div className="relative h-6 flex-1 overflow-hidden rounded bg-ink-100 dark:bg-ink-800">
                <div
                  className={`h-full rounded transition-all duration-700 ${
                    idx === 0
                      ? "bg-gradient-to-r from-brand-500 to-brand-300"
                      : "bg-ink-300 dark:bg-ink-700"
                  }`}
                  style={{ width: `${value}%` }}
                />
              </div>
              <span className="w-14 text-right font-mono text-xs tabular-nums text-ink-700 dark:text-ink-300">
                {value.toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Engineering analysis */}
      <div className="card p-6">
        <div className="flex items-center gap-2.5">
          <div className="grid h-7 w-7 place-items-center rounded-md bg-indigo-50 text-indigo-600 dark:bg-indigo-950/40 dark:text-indigo-300">
            <Wrench size={16} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-ink-900 dark:text-ink-50">
              Engineering analysis
            </h3>
            <p className="text-xs text-ink-500">
              Root cause, mitigation, and process improvements
            </p>
          </div>
        </div>

        <div className="mt-5 grid gap-6 md:grid-cols-2">
          <Section
            title="Likely root causes"
            items={analysis.root_causes}
            accent="brand"
          />
          <Section
            title="Immediate actions"
            items={analysis.immediate_actions}
            accent="emerald"
          />
          <Section
            title="Process improvements"
            items={analysis.process_improvements}
            accent="indigo"
          />
          <div>
            <h4 className="label-mono mb-2">Quality impact</h4>
            <p className="text-sm leading-relaxed text-ink-700 dark:text-ink-300">
              {analysis.quality_impact}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-ink-200 bg-ink-50 px-3 py-2 dark:border-ink-800 dark:bg-ink-950/40">
      <dt className="label-mono">{label}</dt>
      <dd className="mt-0.5 text-sm font-medium text-ink-900 dark:text-ink-100">
        {value}
      </dd>
    </div>
  );
}

function Section({
  title,
  items,
  accent,
}: {
  title: string;
  items: string[];
  accent: "brand" | "emerald" | "indigo";
}) {
  const dot = {
    brand: "bg-brand-500",
    emerald: "bg-emerald-500",
    indigo: "bg-indigo-500",
  }[accent];
  return (
    <div>
      <h4 className="label-mono mb-2">{title}</h4>
      <ul className="space-y-2">
        {items.map((it) => (
          <li
            key={it}
            className="flex items-start gap-2.5 text-sm leading-relaxed text-ink-700 dark:text-ink-300"
          >
            <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${dot}`} />
            <span>{it}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
