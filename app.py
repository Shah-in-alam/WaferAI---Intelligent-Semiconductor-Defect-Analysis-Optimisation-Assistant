"""Gradio entry point for WaferAI."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import gradio as gr
from dotenv import load_dotenv
from PIL import Image

from src import (
    DefectAnalysis,
    WaferAnalyzer,
    WaferClassifier,
    WaferPreprocessor,
    build_pdf_report,
    confidence_chart,
    overlay_gradcam,
)
from src.utils import get_logger, project_root

load_dotenv()
logger = get_logger(__name__)

# ----- Singletons -----
preprocessor = WaferPreprocessor()
classifier = WaferClassifier(model_path=os.getenv("MODEL_PATH"))
analyzer = WaferAnalyzer()

SAMPLE_DIR = project_root() / "data" / "sample_wafers"


def _list_examples() -> list[str]:
    if not SAMPLE_DIR.exists():
        return []
    return sorted(str(p) for p in SAMPLE_DIR.glob("*.png"))


def run_analysis(image: Image.Image | None):
    if image is None:
        return (
            "Upload a wafer map image first.",
            None,
            None,
            None,
            gr.update(value=None, visible=False),
            gr.update(visible=False),
        )

    if not preprocessor.validate_image(image):
        return ("Invalid image.", None, None, None, gr.update(visible=False), gr.update(visible=False))

    tensor = preprocessor.preprocess_for_model(image)
    metadata = preprocessor.extract_metadata(image)

    defect_type, confidence = classifier.predict(tensor)
    probs = classifier.predict_proba(tensor)
    heat = classifier.generate_gradcam(tensor)

    defect_info: dict[str, Any] = {
        "defect_pattern": defect_type,
        "model_confidence": confidence,
        **metadata,
    }

    analysis = analyzer.analyze(defect_info)

    overlay = overlay_gradcam(image, heat)
    chart = confidence_chart(probs)

    report_md = (
        f"**Detected:** {defect_type}  \n"
        f"**Model confidence:** {confidence:.1f}%  \n"
        f"**Location:** {metadata['location']}  •  "
        f"**Defect density:** {metadata['defect_density']}%\n\n"
        + analysis.to_markdown()
    )

    # Generate PDF
    pdf_path = Path(tempfile.gettempdir()) / "waferai_report.pdf"
    build_pdf_report(pdf_path, image, overlay, defect_info, analysis)

    analyzer.reset_chat()

    return (
        report_md,
        overlay,
        chart,
        str(pdf_path),
        gr.update(value=[], visible=True),
        gr.update(visible=True),
    )


def chat_fn(history, user_message):
    if not user_message:
        return history, ""
    answer = analyzer.chat_followup(user_message)
    history = history + [(user_message, answer)]
    return history, ""


def build_ui() -> gr.Blocks:
    examples = _list_examples()

    with gr.Blocks(title="WaferAI", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            "# WaferAI\n"
            "Upload a wafer map image to detect the defect pattern, get an "
            "AI-generated root-cause analysis, and download a PDF report."
        )

        with gr.Row():
            with gr.Column(scale=1):
                image_in = gr.Image(label="Wafer map", type="pil", height=320)
                if examples:
                    gr.Examples(
                        examples=examples,
                        inputs=image_in,
                        label="Sample wafers (from WM-811K)",
                    )
                analyze_btn = gr.Button("Analyse", variant="primary")

            with gr.Column(scale=1):
                overlay_out = gr.Image(label="Model attention (Grad-CAM)", height=320)
                chart_out = gr.Image(label="Class confidence", height=320)

        report_md = gr.Markdown(label="Analysis")

        pdf_out = gr.File(label="Download PDF report", visible=False)

        chat_panel = gr.Group(visible=False)
        with chat_panel:
            gr.Markdown("### Follow-up questions")
            chatbot = gr.Chatbot(height=260)
            with gr.Row():
                chat_in = gr.Textbox(
                    placeholder="Ask about root cause, mitigation, or yield impact…",
                    show_label=False,
                    scale=4,
                )
                send_btn = gr.Button("Send", scale=1)

        analyze_btn.click(
            run_analysis,
            inputs=image_in,
            outputs=[report_md, overlay_out, chart_out, pdf_out, chatbot, chat_panel],
        )
        chat_in.submit(chat_fn, inputs=[chatbot, chat_in], outputs=[chatbot, chat_in])
        send_btn.click(chat_fn, inputs=[chatbot, chat_in], outputs=[chatbot, chat_in])

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True)
