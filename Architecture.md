# 🏗 WaferAI — System Architecture

This document describes the technical architecture of WaferAI, including data flow, component design, and design decisions.

---

## 📐 High-Level Architecture

```
                    ┌─────────────────────────────────────┐
                    │         END USER                    │
                    │   (Process Engineer / Operator)     │
                    └──────────────┬──────────────────────┘
                                   │
                                   │ HTTPS
                                   ▼
                    ┌─────────────────────────────────────┐
                    │      PRESENTATION LAYER             │
                    │         (Gradio Web UI)             │
                    │                                     │
                    │   • Image upload                    │
                    │   • Results display                 │
                    │   • Interactive chat                │
                    │   • PDF download                    │
                    └──────────────┬──────────────────────┘
                                   │
                                   │ Function calls
                                   ▼
        ┌──────────────────────────┴──────────────────────────┐
        │                                                     │
        ▼                                                     ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│   PREPROCESSING LAYER    │              │  VISUALISATION LAYER     │
│      (OpenCV / PIL)      │              │   (Matplotlib/Plotly)    │
│                          │              │                          │
│ • Resize images          │              │ • Grad-CAM heatmaps      │
│ • Normalise pixel values │              │ • Confidence bar charts  │
│ • Metadata extraction    │              │ • Defect statistics      │
└────────────┬─────────────┘              └──────────────────────────┘
             │
             │ Tensor (1, 96, 96, 3)
             ▼
┌──────────────────────────────────────────┐
│         MODEL INFERENCE LAYER            │
│        (TensorFlow / EfficientNetB0)     │
│                                          │
│   • CNN Classification                   │
│   • Confidence scores per class          │
│   • Feature map extraction               │
└────────────┬─────────────────────────────┘
             │
             │ {defect_type, confidence, metadata}
             ▼
┌──────────────────────────────────────────┐
│         AI REASONING LAYER               │
│         (Anthropic Claude API)           │
│                                          │
│   • Root cause analysis                  │
│   • Action recommendations               │
│   • Yield impact estimation              │
└────────────┬─────────────────────────────┘
             │
             │ Structured response (Pydantic)
             ▼
┌──────────────────────────────────────────┐
│         OUTPUT LAYER                     │
│                                          │
│   • Formatted markdown response          │
│   • PDF report (ReportLab)               │
│   • Logged analytics                     │
└──────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### Step 1: Image Upload
- User uploads a wafer map image via Gradio interface
- Supported formats: PNG, JPG, JPEG, BMP
- Maximum size: 10 MB

### Step 2: Preprocessing Pipeline

```
Input Image (any size, any channels)
    ↓
Convert to RGB (3 channels)
    ↓
Resize to 96×96 pixels
    ↓
Normalise pixel values to [0, 1]
    ↓
Add batch dimension → (1, 96, 96, 3)
    ↓
Output: NumPy tensor ready for model
```

**Parallel metadata extraction:**
- Defect density (% of pixels with defects)
- Primary defect location (centre vs edge)
- Image dimensions

### Step 3: Classification Inference

```
Tensor (1, 96, 96, 3)
    ↓
EfficientNetB0 backbone (frozen)
    ↓
GlobalAveragePooling2D
    ↓
Dense(256, ReLU) + Dropout(0.2)
    ↓
Dense(9, Softmax)
    ↓
Output: probabilities array [0.02, 0.85, 0.01, ..., 0.03]
```

**Postprocessing:**
- Get top-1 prediction class
- Calculate confidence score
- Generate Grad-CAM heatmap for explainability

### Step 4: LLM Analysis

The classifier output is sent to Claude with a structured prompt:

```json
{
  "defect_pattern": "Center",
  "model_confidence": 96.4,
  "defect_density": 12.3,
  "location": "Centre"
}
```

Claude responds with structured JSON:

```json
{
  "defect_type": "Center",
  "severity": "High",
  "root_causes": [
    "Photolithography focus drift",
    "Resist coating non-uniformity",
    "Chamber pressure fluctuation"
  ],
  "immediate_actions": [
    "Recalibrate stepper focus",
    "Inspect resist dispense nozzle",
    "Verify chamber pressure sensors"
  ],
  "process_improvements": [
    "Implement closed-loop focus control",
    "Add inline coating uniformity monitor",
    "Upgrade chamber pressure regulation"
  ],
  "quality_impact": "Center defects directly affect ...",
  "estimated_yield_loss": "8-15%"
}
```

### Step 5: Output Generation

- Formatted markdown displayed in Gradio UI
- PDF report generated on demand (ReportLab)
- All analyses logged for future reference

---

## 🧩 Component Architecture

### 1. Classifier Module (`src/classifier.py`)

**Responsibilities:**
- Load and manage the trained CNN model
- Perform inference on preprocessed images
- Generate Grad-CAM visualisations
- Cache model in memory for performance

**Key Classes:**
```python
class WaferClassifier:
    def __init__(self, model_path: str)
    def predict(self, image: np.ndarray) -> tuple[str, float]
    def predict_proba(self, image: np.ndarray) -> dict[str, float]
    def generate_gradcam(self, image: np.ndarray) -> np.ndarray
```

### 2. Preprocessor Module (`src/preprocessor.py`)

**Responsibilities:**
- Standardise image formats and sizes
- Extract metadata from raw wafer images
- Apply normalisation transformations

**Key Classes:**
```python
class WaferPreprocessor:
    def preprocess_for_model(self, image: PIL.Image) -> np.ndarray
    def extract_metadata(self, image: PIL.Image) -> dict
    def validate_image(self, image: PIL.Image) -> bool
```

### 3. Analyzer Module (`src/analyzer.py`)

**Responsibilities:**
- Build structured prompts for Claude
- Manage API communication
- Parse and validate LLM responses
- Handle retries and errors

**Key Classes:**
```python
class WaferAnalyzer:
    def __init__(self, api_key: str, model: str)
    def analyze(self, defect_info: dict) -> DefectAnalysis
    def chat_followup(self, question: str, context: dict) -> str
```

### 4. Visualisation Module (`src/visualization.py`)

**Responsibilities:**
- Generate Grad-CAM heatmaps
- Create confidence bar charts
- Build interactive Plotly dashboards

### 5. Report Generator (`src/report_generator.py`)

**Responsibilities:**
- Format analysis results into professional PDF
- Include images, charts, and recommendations
- Support custom branding

---

## 🎨 Design Decisions

### Why EfficientNetB0?

We compared multiple architectures:

| Model | Accuracy | Size | Inference |
|-------|----------|------|-----------|
| MobileNetV2 | 91.3% | 14 MB | 8 ms |
| ResNet50 | 94.7% | 98 MB | 28 ms |
| **EfficientNetB0** | **96.4%** | **29 MB** | **22 ms** |
| EfficientNetB3 | 97.1% | 48 MB | 45 ms |

**EfficientNetB0** offered the best balance of accuracy, size, and speed for our use case.

### Why Claude over GPT-4?

| Factor | Claude Sonnet 4.5 | GPT-4 Turbo |
|--------|-------------------|-------------|
| Long-context understanding | Excellent | Very Good |
| Structured outputs | Excellent | Good |
| Technical reasoning | Excellent | Very Good |
| API simplicity | Cleaner | More complex |
| Cost (per analysis) | ~$0.01 | ~$0.02 |

Claude's strong reasoning and clean API made it the better choice for this technical domain. The system is modular, so swapping to other LLMs requires minimal changes.

### Why Gradio over Streamlit/Flask?

- **Faster to build** — designed specifically for ML demos
- **Beautiful by default** — minimal CSS work needed
- **Free deployment** — Hugging Face Spaces integration
- **Built-in features** — image upload, examples, sharing

### Why 96×96 Image Size?

- Original wafer maps vary from 26×26 to 200×200
- 96×96 preserves enough detail for pattern recognition
- Balances accuracy with inference speed
- Matches EfficientNet's preferred input range

### Class Imbalance Strategy

The WM-811K dataset is severely imbalanced:
- "None" class: ~78%
- "Edge-Ring": ~7%
- Other classes: 1-5% each

**Solutions applied:**
1. Class weights in loss function (most effective)
2. Data augmentation for minority classes
3. Stratified train/val/test splits

---

## 🔐 Security & Privacy

- **API keys** stored in environment variables, never committed
- **No user data** stored on servers (stateless application)
- **HTTPS** enforced on all deployments
- **Rate limiting** on API calls to prevent abuse
- **Input validation** on all uploaded images

---

## ⚡ Performance Optimisations

- **Model caching** — Loaded once at startup
- **Batch inference** — Multiple images processed together when possible
- **Async API calls** — Non-blocking Claude API requests
- **Response caching** — Identical inputs return cached results
- **Lazy imports** — Heavy libraries loaded only when needed

**Benchmarks (on Hugging Face free tier):**
- Image upload to first result: ~3 seconds
- Full analysis with Claude: ~5-7 seconds
- PDF generation: ~1 second

---

## 📦 Deployment Architecture

### Local Development
```
Developer Machine
├── Python venv
├── Local Gradio (port 7860)
└── .env with API key
```

### Production (Hugging Face Spaces)
```
Hugging Face Cloud
├── Gradio Space (CPU tier — free)
├── Model loaded from Spaces storage
├── API key stored as secret
└── Public URL with HTTPS
```

### Docker Deployment (alternative)
```
Docker Container
├── Python 3.10 base image
├── All dependencies pre-installed
├── Model included in image
├── Environment variables injected
└── Exposed port 7860
```

---

## 🧪 Testing Strategy

- **Unit tests** — Each module tested in isolation
- **Integration tests** — End-to-end workflow verification
- **Model validation** — Performance metrics on held-out test set
- **API mocking** — Claude responses mocked for fast tests
- **Manual UAT** — Real wafer images tested by user

---

## 🔮 Scalability Considerations

If deployed at scale, the architecture would evolve:

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
       ┌──────▼──────┐ ┌────▼──────┐ ┌─────▼─────┐
       │ Web Server  │ │Web Server │ │Web Server │
       │ (Gradio)    │ │ (Gradio)  │ │ (Gradio)  │
       └──────┬──────┘ └────┬──────┘ └─────┬─────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼────────┐
                    │  Model Service  │
                    │  (TF Serving)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Redis Cache   │
                    │   (responses)   │
                    └─────────────────┘
```

---

## 📝 Code Quality Standards

- **Type hints** on all functions
- **Docstrings** following Google style
- **Pydantic models** for data validation
- **Logging** with structured format
- **Error handling** with custom exceptions
- **Pre-commit hooks** for linting (ruff, black, mypy)

---

*Last updated: May 2026*
