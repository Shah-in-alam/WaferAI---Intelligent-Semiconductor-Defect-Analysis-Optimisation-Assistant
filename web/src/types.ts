export interface Health {
  status: string;
  using_stub_classifier: boolean;
  claude_configured: boolean;
  claude_model?: string;
  sample_count: number;
}

export interface DefectAnalysis {
  defect_type: string;
  severity: "Low" | "Medium" | "High" | "Critical" | string;
  root_causes: string[];
  immediate_actions: string[];
  process_improvements: string[];
  quality_impact: string;
  estimated_yield_loss: string;
}

export interface Metadata {
  width: number;
  height: number;
  defect_density: number;
  location: string;
}

export interface AnalysisResult {
  defect_type: string;
  confidence: number;
  probabilities: Record<string, number>;
  metadata: Metadata;
  analysis: DefectAnalysis;
  overlay_png_b64: string;
  pdf_b64: string;
}
