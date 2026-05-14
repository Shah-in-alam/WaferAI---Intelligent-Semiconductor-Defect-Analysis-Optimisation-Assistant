import { useEffect, useRef, useState } from "react";
import { Upload, Image as ImageIcon, Loader2, Sparkles, X } from "lucide-react";
import { listSamples, sampleUrl } from "../api";

interface Props {
  onAnalyze: (file: File) => void;
  onAnalyzeSample: (name: string) => void;
  loading: boolean;
}

export function UploadPanel({ onAnalyze, onAnalyzeSample, loading }: Props) {
  const [samples, setSamples] = useState<string[]>([]);
  const [preview, setPreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => {
    listSamples()
      .then(setSamples)
      .catch(() => setSamples([]));
  }, []);

  function handleFile(file: File) {
    setSelectedFile(file);
    setPreview(URL.createObjectURL(file));
  }

  function clear() {
    setPreview(null);
    setSelectedFile(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <section className="card overflow-hidden">
      <div className="flex items-center justify-between border-b border-ink-200 px-6 py-4 dark:border-ink-800">
        <div className="flex items-center gap-2.5">
          <div className="grid h-7 w-7 place-items-center rounded-md bg-brand-50 text-brand-600 dark:bg-brand-950/40 dark:text-brand-300">
            <ImageIcon size={16} />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-ink-900 dark:text-ink-50">
              Wafer image
            </h2>
            <p className="text-xs text-ink-500">
              Upload or pick a real WM-811K sample
            </p>
          </div>
        </div>
        <span className="label-mono">Step 01</span>
      </div>

      <div className="p-6">
        <label
          htmlFor="file-input"
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            const f = e.dataTransfer.files[0];
            if (f) handleFile(f);
          }}
          className={`group relative flex aspect-[16/9] cursor-pointer flex-col items-center justify-center overflow-hidden rounded-xl border-2 border-dashed transition ${
            dragOver
              ? "border-brand-400 bg-brand-50/60 ring-soft dark:bg-brand-950/30"
              : "border-ink-200 bg-ink-50 hover:border-brand-300 hover:bg-brand-50/40 dark:border-ink-700 dark:bg-ink-950/40 dark:hover:border-brand-700 dark:hover:bg-brand-950/30"
          }`}
        >
          {preview ? (
            <>
              <img
                src={preview}
                alt="uploaded"
                className="max-h-full max-w-full rounded object-contain"
              />
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  clear();
                }}
                disabled={loading}
                className="absolute right-3 top-3 grid h-7 w-7 place-items-center rounded-full bg-ink-900/70 text-white opacity-0 transition group-hover:opacity-100"
              >
                <X size={14} />
              </button>
            </>
          ) : (
            <div className="flex flex-col items-center gap-2 text-ink-500 dark:text-ink-400">
              <div className="grid h-12 w-12 place-items-center rounded-full bg-white shadow-soft dark:bg-ink-800">
                <Upload size={20} className="text-brand-500" />
              </div>
              <span className="text-sm font-medium text-ink-700 dark:text-ink-200">
                Drop a wafer map here
              </span>
              <span className="text-xs">or click to browse · PNG · JPG · BMP</span>
            </div>
          )}
          <input
            ref={inputRef}
            id="file-input"
            type="file"
            accept="image/*"
            className="sr-only"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />
        </label>

        <div className="mt-4 flex justify-end gap-2">
          <button
            className="btn-secondary"
            onClick={clear}
            disabled={!preview || loading}
          >
            Clear
          </button>
          <button
            className="btn-primary"
            disabled={!selectedFile || loading}
            onClick={() => selectedFile && onAnalyze(selectedFile)}
          >
            {loading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Sparkles size={14} />
            )}
            {loading ? "Analysing…" : "Analyse"}
          </button>
        </div>

        {samples.length > 0 && (
          <>
            <div className="mt-8 flex items-center justify-between">
              <p className="label-mono">WM-811K samples</p>
              <p className="text-xs text-ink-400">Click to analyse instantly</p>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2.5 sm:grid-cols-5 lg:grid-cols-9">
              {samples.map((name) => (
                <button
                  key={name}
                  disabled={loading}
                  onClick={() => onAnalyzeSample(name)}
                  className="group/thumb relative aspect-square overflow-hidden rounded-lg border border-ink-200 bg-white transition hover:-translate-y-0.5 hover:border-brand-400 hover:shadow-elevated disabled:opacity-50 dark:border-ink-800 dark:bg-ink-900"
                  title={name.replace(".png", "")}
                >
                  <img
                    src={sampleUrl(name)}
                    alt={name}
                    className="absolute inset-0 h-full w-full object-cover"
                  />
                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-ink-900/80 to-transparent p-1.5">
                    <span className="block truncate text-[10px] font-medium text-white">
                      {name.replace(".png", "").replace("_", "-")}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
}
