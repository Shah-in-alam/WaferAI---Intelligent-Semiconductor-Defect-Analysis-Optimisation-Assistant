import type { AnalysisResult, Health } from "./types";

export async function getHealth(): Promise<Health> {
  const r = await fetch("/api/health");
  if (!r.ok) throw new Error(`Health check failed: ${r.status}`);
  return r.json();
}

export async function listSamples(): Promise<string[]> {
  const r = await fetch("/api/samples");
  if (!r.ok) throw new Error(`Listing samples failed: ${r.status}`);
  return r.json();
}

export function sampleUrl(name: string): string {
  return `/api/samples/${encodeURIComponent(name)}`;
}

/** Decode a base64-encoded PDF and return a blob: URL the browser can download. */
export function pdfBlobUrl(b64: string): string {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return URL.createObjectURL(new Blob([bytes], { type: "application/pdf" }));
}

export async function analyzeFile(file: File): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("image", file);
  const r = await fetch("/api/analyze", { method: "POST", body: form });
  if (!r.ok) {
    const msg = await r.text().catch(() => "");
    throw new Error(`Analyze failed (${r.status}): ${msg}`);
  }
  return r.json();
}

export async function analyzeSample(name: string): Promise<AnalysisResult> {
  const r = await fetch(sampleUrl(name));
  if (!r.ok) throw new Error(`Could not fetch sample ${name}`);
  const blob = await r.blob();
  const file = new File([blob], name, { type: "image/png" });
  return analyzeFile(file);
}

/** Stream chat tokens. Yields each text chunk as it arrives via SSE. */
export async function* streamChat(message: string): AsyncGenerator<string> {
  const r = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!r.ok || !r.body) {
    throw new Error(`Chat request failed: ${r.status}`);
  }

  const reader = r.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE: events delimited by blank line. Each event has lines like
    //   event: <type>
    //   data: <payload>
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      let event = "message";
      const dataLines: string[] = [];
      for (const line of part.split("\n")) {
        if (line.startsWith("event:")) {
          event = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).trim());
        }
      }
      const raw = dataLines.join("\n");
      if (event === "done") return;
      if (event === "token" || event === "error") {
        try {
          const decoded = JSON.parse(raw) as string;
          yield decoded;
        } catch {
          if (raw) yield raw;
        }
      }
    }
  }
}
