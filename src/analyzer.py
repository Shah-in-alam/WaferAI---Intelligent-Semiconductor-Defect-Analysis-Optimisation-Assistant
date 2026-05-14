from __future__ import annotations

import json
import os
from typing import Any, Optional

from pydantic import BaseModel, Field

from .recommendations import fallback_recommendations
from .utils import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a senior semiconductor process engineer with 20 years of experience at \
photolithography fabs (ASML / TSMC scale). Given a detected wafer defect pattern, you return \
concise, actionable analysis grounded in real fab practice. Be specific about tooling, recipe \
parameters, and likely root-cause categories. Estimate yield loss as a percentage range based on \
defect type and density."""

PROMPT_TEMPLATE = """A wafer inspection system has detected the following defect pattern. \
Analyse it and return a structured root-cause and recommendation set.

Detected pattern: {defect_pattern}
Model confidence: {model_confidence:.1f}%
Approximate defect density (pixels above threshold): {defect_density}%
Primary location: {location}
Image dimensions: {width}x{height} px

Return your analysis as JSON conforming to the schema."""


class DefectAnalysis(BaseModel):
    defect_type: str
    severity: str = Field(..., description='One of: "Low", "Medium", "High", "Critical"')
    root_causes: list[str] = Field(..., min_length=1, max_length=6)
    immediate_actions: list[str] = Field(..., min_length=1, max_length=6)
    process_improvements: list[str] = Field(..., min_length=1, max_length=6)
    quality_impact: str
    estimated_yield_loss: str = Field(..., description='Range like "5-10%"')

    def to_markdown(self) -> str:
        def bullets(items: list[str]) -> str:
            return "\n".join(f"- {it}" for it in items)

        return (
            f"### Defect Analysis: {self.defect_type}\n\n"
            f"**Severity:** {self.severity}  \n"
            f"**Estimated Yield Loss:** {self.estimated_yield_loss}\n\n"
            f"#### Likely Root Causes\n{bullets(self.root_causes)}\n\n"
            f"#### Immediate Actions\n{bullets(self.immediate_actions)}\n\n"
            f"#### Process Improvements\n{bullets(self.process_improvements)}\n\n"
            f"#### Quality Impact\n{self.quality_impact}\n"
        )


class WaferAnalyzer:
    """Wraps Claude for structured defect analysis and follow-up Q&A.

    If `ANTHROPIC_API_KEY` is missing or the API call fails, falls back to the
    rules-based knowledge base in `recommendations.py` so the demo always
    returns a result.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-opus-4-7")
        self.client = self._init_client()
        self._last_context: dict[str, Any] | None = None
        self._chat_history: list[dict[str, Any]] = []

    def _init_client(self):
        if not self.api_key:
            logger.info("ANTHROPIC_API_KEY not set — analyzer will use rules-based fallback.")
            return None
        try:
            import anthropic

            return anthropic.Anthropic(api_key=self.api_key)
        except Exception as exc:
            logger.warning("Failed to initialise Anthropic client (%s) — using fallback.", exc)
            return None

    def analyze(self, defect_info: dict[str, Any]) -> DefectAnalysis:
        if self.client is None:
            analysis = self._fallback(defect_info)
            self._save_context(defect_info, analysis)
            return analysis

        prompt = PROMPT_TEMPLATE.format(
            defect_pattern=defect_info.get("defect_pattern", "Unknown"),
            model_confidence=float(defect_info.get("model_confidence", 0.0)),
            defect_density=defect_info.get("defect_density", 0.0),
            location=defect_info.get("location", "Unknown"),
            width=defect_info.get("width", 0),
            height=defect_info.get("height", 0),
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": DefectAnalysis.model_json_schema(),
                    }
                },
                messages=[{"role": "user", "content": prompt}],
            )
            text = next(b.text for b in response.content if b.type == "text")
            analysis = DefectAnalysis(**json.loads(text))
            self._save_context(defect_info, analysis)
            return analysis
        except Exception as exc:
            logger.warning("Claude analysis failed (%s) — using fallback.", exc)
            analysis = self._fallback(defect_info)
            self._save_context(defect_info, analysis)
            return analysis

    def stream_chat(self, question: str):
        """Generator yielding text chunks of a Claude streaming response.

        Falls back to a static message when no API key is configured or no
        prior analysis has been run.
        """
        if self.client is None:
            yield "Follow-up chat needs an Anthropic API key. Set ANTHROPIC_API_KEY in `.env` to enable it."
            return
        if self._last_context is None:
            yield "Run an analysis first, then ask a follow-up about it."
            return

        self._chat_history.append({"role": "user", "content": question})
        context_blob = (
            "Most recent wafer analysis context:\n"
            f"{json.dumps(self._last_context, indent=2)}\n\n"
            "Answer the engineer's follow-up question in 2-4 sentences. "
            "Be concrete; cite specific tools or process steps where helpful."
        )
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=512,
                system=SYSTEM_PROMPT + "\n\n" + context_blob,
                messages=self._chat_history,
            ) as stream:
                pieces: list[str] = []
                for text in stream.text_stream:
                    pieces.append(text)
                    yield text
            self._chat_history.append({"role": "assistant", "content": "".join(pieces)})
        except Exception as exc:
            logger.warning("Streaming chat failed (%s).", exc)
            yield f"\n\n[error: {exc}]"

    def chat_followup(self, question: str) -> str:
        if self.client is None:
            return (
                "Follow-up chat needs an Anthropic API key. "
                "Set ANTHROPIC_API_KEY in `.env` to enable it."
            )
        if self._last_context is None:
            return "Run an analysis first, then ask a follow-up about it."

        self._chat_history.append({"role": "user", "content": question})

        context_blob = (
            "Most recent wafer analysis context:\n"
            f"{json.dumps(self._last_context, indent=2)}\n\n"
            "Answer the engineer's follow-up question in 2-4 sentences. "
            "Be concrete; cite specific tools or process steps where helpful."
        )
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=SYSTEM_PROMPT + "\n\n" + context_blob,
                messages=self._chat_history,
            )
            answer = next(b.text for b in response.content if b.type == "text")
            self._chat_history.append({"role": "assistant", "content": answer})
            return answer
        except Exception as exc:
            logger.warning("Follow-up chat failed (%s).", exc)
            return f"Sorry, the LLM call failed: {exc}"

    def reset_chat(self) -> None:
        self._chat_history.clear()

    def _save_context(self, defect_info: dict, analysis: DefectAnalysis) -> None:
        self._last_context = {
            "defect_info": defect_info,
            "analysis": analysis.model_dump(),
        }
        self._chat_history.clear()

    @staticmethod
    def _fallback(defect_info: dict[str, Any]) -> DefectAnalysis:
        data = fallback_recommendations(defect_info.get("defect_pattern", "None"))
        return DefectAnalysis(**data)
