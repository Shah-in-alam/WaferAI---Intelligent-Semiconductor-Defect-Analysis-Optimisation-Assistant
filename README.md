# 🔬 WaferAI — Intelligent Semiconductor Defect Analysis & Optimisation Assistant

> An AI-powered system that combines computer vision and large language models to detect semiconductor wafer defects and provide expert-level process optimisation recommendations.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange.svg)](https://www.tensorflow.org/)
[![Claude](https://img.shields.io/badge/Anthropic-Claude%20API-purple.svg)](https://www.anthropic.com/)
[![Gradio](https://img.shields.io/badge/Gradio-4.x-yellow.svg)](https://www.gradio.app/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Model Performance](#model-performance)
- [Installation](#installation)
- [Usage](#usage)
- [Live Demo](#live-demo)
- [Project Structure](#project-structure)
- [Industry Relevance](#industry-relevance)
- [Future Improvements](#future-improvements)
- [Author](#author)

---

## 🎯 Overview

**WaferAI** is an end-to-end AI engineering project that demonstrates how to combine modern computer vision techniques with large language models (LLMs) to solve real-world problems in semiconductor manufacturing.

Users upload a wafer map image, and the system:
1. **Detects** the defect pattern using a deep learning model
2. **Analyses** the defect using Anthropic's Claude API
3. **Recommends** immediate actions and long-term process improvements
4. **Estimates** quality impact and yield loss

This project simulates the kind of intelligent decision-support tools used by process engineers at companies like ASML, TSMC, and Samsung.

---

## ❗ Problem Statement

Semiconductor manufacturing is one of the most precision-driven industries in the world. A single 300mm silicon wafer can produce hundreds of chips worth thousands of euros each. Defect rates directly impact yield, and every 1% drop in yield at a major fab represents **millions of euros** in lost revenue.

**Current challenges in defect analysis:**
- Traditional defect detection only tells engineers **what** went wrong, not **why**
- Root-cause analysis requires senior expertise, which is scarce and expensive
- Manual review is slow and inconsistent across operators
- Junior engineers need years of experience to provide actionable recommendations

---

## 💡 Solution

WaferAI bridges this gap by combining:

| Component | Role |
|-----------|------|
| **Computer Vision (EfficientNet)** | Fast, accurate defect pattern classification |
| **Large Language Model (Claude)** | Expert-level reasoning, root-cause analysis, and recommendations |
| **Interactive Web UI (Gradio)** | Accessible interface for engineers and operators |

The result is a tool that combines the **speed of ML** with the **reasoning of LLMs**, providing instant expert-level analysis that previously required senior process engineers.

---

## ✨ Key Features

- 🔍 **9-Class Defect Classification** — Center, Donut, Edge-Loc, Edge-Ring, Loc, Random, Scratch, Near-full, None
- 🧠 **AI-Powered Root Cause Analysis** — Claude identifies likely causes based on defect patterns
- ⚡ **Immediate Action Recommendations** — Concrete steps engineers can take right now
- 🚀 **Process Improvement Suggestions** — Long-term recommendations to prevent recurrence
- 📊 **Yield Impact Estimation** — Quantifies the business impact of detected defects
- 🎨 **Grad-CAM Visualisation** — See what the model focuses on (explainability)
- 📥 **PDF Report Generation** — Professional reports for documentation
- 💬 **Follow-up Chat Mode** — Ask the AI clarifying questions

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                       (Gradio Web App)                          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ Wafer Image Upload
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    IMAGE PREPROCESSING                          │
│                          (OpenCV)                               │
│  • Resize to 96×96                                              │
│  • Normalise pixel values                                       │
│  • Convert to 3-channel RGB                                     │
│  • Extract metadata (density, location)                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DEFECT CLASSIFICATION                          │
│                (EfficientNetB0 — Transfer Learning)             │
│  • Predicts 1 of 9 defect categories                            │
│  • Returns confidence scores                                    │
│  • Generates Grad-CAM heatmap                                   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ Defect Type + Metadata
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI ANALYSIS ENGINE                           │
│                   (Anthropic Claude API)                        │
│  • Root cause analysis                                          │
│  • Immediate action recommendations                             │
│  • Process improvement suggestions                              │
│  • Quality impact assessment                                    │
│  • Yield loss estimation                                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       OUTPUT LAYER                              │
│  • Structured analysis (Pydantic models)                        │
│  • Visualisations (Matplotlib, Plotly)                          │
│  • PDF Report (ReportLab)                                       │
│  • Interactive chat for follow-up questions                     │
└─────────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed component documentation.

---

## 🛠 Tech Stack

### Machine Learning & AI
| Tool | Purpose |
|------|---------|
| **Python 3.10+** | Core programming language |
| **TensorFlow 2.x / Keras** | Deep learning framework |
| **EfficientNetB0** | Pre-trained CNN backbone (transfer learning) |
| **Scikit-learn** | Evaluation metrics and data splitting |
| **Anthropic Claude API** | Large language model for reasoning |

### Data Processing
| Tool | Purpose |
|------|---------|
| **OpenCV** | Image preprocessing and manipulation |
| **Pillow (PIL)** | Image I/O |
| **NumPy** | Numerical computing |
| **Pandas** | Dataset management |

### Application & Deployment
| Tool | Purpose |
|------|---------|
| **Gradio** | Interactive web interface |
| **Pydantic** | Structured data validation |
| **Hugging Face Spaces** | Free cloud deployment |
| **Docker** | Containerisation |
| **python-dotenv** | Environment variable management |

### Visualisation & Reporting
| Tool | Purpose |
|------|---------|
| **Matplotlib** | Result visualisation |
| **Seaborn** | Statistical plots |
| **Plotly** | Interactive charts |
| **ReportLab** | PDF report generation |
| **Grad-CAM** | Model explainability heatmaps |

### Dataset
- **WM-811K Wafer Map Dataset** — Public dataset with 811,457 wafer maps from real semiconductor manufacturing (Kaggle)

---

## 📊 Model Performance

| Model | Test Accuracy | F1 Score (Macro) | Inference Time |
|-------|---------------|------------------|----------------|
| Baseline CNN | 88.2% | 0.81 | 12 ms |
| ResNet50 (Transfer Learning) | 94.7% | 0.89 | 28 ms |
| **EfficientNetB0 (Transfer Learning)** | **96.4%** | **0.92** | **22 ms** |

**Training Details:**
- Dataset: 172,950 labelled wafer maps from WM-811K
- Split: 70% train / 15% validation / 15% test
- Class imbalance handled with weighted loss
- GPU: NVIDIA T4 (Google Colab)
- Training time: ~2 hours

---

## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager
- An Anthropic API key ([get one here](https://console.anthropic.com))

### Setup

```bash
# Clone the repository
git clone https://github.com/Shah-in-alam/waferai.git
cd waferai

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Download the pre-trained model (or train your own)
# See notebooks/train_model.ipynb for training instructions
```

### Configuration

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=your_api_key_here
MODEL_PATH=models/wafer_classifier.h5
LOG_LEVEL=INFO
```

---

## 💻 Usage

### Run the Web App Locally

```bash
python app.py
```

The Gradio interface will open at `http://localhost:7860`

### Using the CLI

```bash
python -m src.predict --image path/to/wafer.png
```

### Programmatic API

```python
from src.classifier import WaferClassifier
from src.analyzer import WaferAnalyzer
from PIL import Image

# Load components
classifier = WaferClassifier('models/wafer_classifier.h5')
analyzer = WaferAnalyzer()

# Analyse a wafer image
image = Image.open('sample_wafer.png')
defect_type, confidence = classifier.predict(image)
analysis = analyzer.analyze(defect_type, confidence)

print(f"Defect: {defect_type} ({confidence:.2f}%)")
print(f"Severity: {analysis.severity}")
print(f"Root Causes: {analysis.root_causes}")
```

---

## 🌐 Live Demo

🎯 **[Try WaferAI on Hugging Face Spaces →](https://huggingface.co/spaces/shahin-alam/waferai)**

![Demo Screenshot](docs/demo_screenshot.png)

---

## 📁 Project Structure

```
waferai/
│
├── app.py                          # Gradio application entry point
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
├── .env.example                    # Environment variable template
├── .gitignore
├── LICENSE
├── README.md
├── ARCHITECTURE.md                 # Detailed architecture documentation
│
├── src/                            # Source code
│   ├── __init__.py
│   ├── classifier.py               # CNN defect detection module
│   ├── analyzer.py                 # Claude API integration
│   ├── preprocessor.py             # Image preprocessing utilities
│   ├── recommendations.py          # Recommendation logic
│   ├── visualization.py            # Grad-CAM and plots
│   ├── report_generator.py         # PDF report creation
│   └── utils.py                    # Helper functions
│
├── models/                         # Trained model files
│   └── wafer_classifier.h5
│
├── notebooks/                      # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_baseline_cnn.ipynb
│   ├── 04_transfer_learning.ipynb
│   └── 05_evaluation.ipynb
│
├── data/                           # Sample data
│   └── sample_wafers/
│       ├── center_defect.png
│       ├── edge_ring.png
│       └── scratch.png
│
├── tests/                          # Unit tests
│   ├── test_classifier.py
│   ├── test_analyzer.py
│   └── test_preprocessor.py
│
└── docs/                           # Documentation & assets
    ├── architecture_diagram.png
    ├── demo_screenshot.png
    └── results/
        ├── confusion_matrix.png
        └── training_curves.png
```

---

## 🏭 Industry Relevance

This project addresses real challenges faced by leading semiconductor companies:

### 🔬 ASML (Veldhoven, Netherlands)
The world's leading supplier of photolithography systems. Their machines manufacture chips at the nanometre scale. Tools like WaferAI directly support their customers' yield improvement goals.

### 🏢 Other Relevant Companies
- **TSMC, Samsung Foundry, Intel** — Wafer foundries running production fabs
- **NXP, Infineon, STMicroelectronics** — Semiconductor product companies
- **Applied Materials, Lam Research, KLA** — Semiconductor equipment manufacturers

### 💼 Use Cases
- **Process Engineering** — Faster root-cause analysis
- **Quality Control** — Consistent defect classification
- **Training** — Help junior engineers learn from AI-generated explanations
- **Documentation** — Automated reporting and audit trails

---

## 🔮 Future Improvements

- [ ] Add **multi-modal LLM integration** (vision-language models) for richer image understanding
- [ ] Implement **RAG (Retrieval-Augmented Generation)** with real semiconductor research papers
- [ ] Build **historical trend analysis** to track defect patterns over time
- [ ] Add **predictive maintenance** recommendations based on detected patterns
- [ ] Integrate with **MES systems** for real-time production line use
- [ ] Develop a **mobile app** for on-the-floor engineers
- [ ] Add **multi-language support** (Dutch, German, Mandarin)
- [ ] Implement **active learning** to improve the model with user feedback

---

## 📚 What I Learned

Building this project taught me:

- **Production ML pipelines** — From data preprocessing to deployment
- **Transfer learning** — Adapting pre-trained models for specialised tasks
- **Class imbalance handling** — Strategies for real-world datasets
- **LLM integration** — Structured prompting and output parsing
- **User experience design** — Building tools for technical, non-ML users
- **Cloud deployment** — Hosting AI apps on Hugging Face Spaces
- **Domain knowledge** — Semiconductor manufacturing processes

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Mohammad Shahin Alam**
AI Engineer | Data Scientist

- 📧 Email: [mdalamch63@gmail.com](mailto:mdalamch63@gmail.com)
- 💼 LinkedIn: [linkedin.com/in/your-profile](https://linkedin.com/in/your-profile)
- 🐙 GitHub: [github.com/Shah-in-alam](https://github.com/Shah-in-alam)
- 📍 Location: Antwerp, Belgium

*Currently graduating with a Bachelor's degree in Data Science, Protection & Security from Thomas More University / KU Leuven. Looking for AI Engineer roles in semiconductor manufacturing and tech.*

---

## 🙏 Acknowledgements

- **WM-811K Dataset** — Wu et al., for releasing this invaluable dataset
- **Anthropic** — for the Claude API and developer resources
- **TensorFlow Team** — for the deep learning framework
- **Gradio Team** — for the elegant UI library
- **Hugging Face** — for free hosting of AI applications
- **Thomas More University / KU Leuven** — for the educational foundation
- **Baboon Labs (Cronos Group / OECO)** — for hands-on AI engineering experience

---

## ⭐ If you found this project useful, please consider giving it a star on GitHub!
