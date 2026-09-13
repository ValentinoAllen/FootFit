# FootFit 👟📏

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-green.svg)](https://opencv.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-ee4c2c.svg)](https://pytorch.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**FootFit** is an AI-powered Computer Vision system designed to accurately measure human foot dimensions (length, width, arch profile) from standard digital images using reference objects or calibrated camera setups. By bridging the gap between digital foot measurement and brand-specific shoe sizing parameters, FootFit delivers precise shoe size recommendations to minimize size uncertainty in e-commerce applications.

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [System Architecture & CV Pipeline](#-system-architecture--cv-pipeline)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
  - [Local Python Environment](#1-local-python-environment)
  - [Docker Containerization](#2-docker-containerization)
- [API Endpoint Documentation](#-api-endpoint-documentation)
- [Usage Guide](#-usage-guide)
- [License](#-license)

---

## ✨ Key Features

- **Reference-Based Homography Calibration:** Calculates perspective correction matrices using known reference objects (e.g., A4 paper, standard credit card) to rectify camera tilt and distortion.
- **High-Precision Foot Landmark Segmentation:** Employs Deep Learning segmentation models combined with anatomical landmark detection to locate critical keypoints: heel posterior point, longest distal phalanx (toe), and 1st/5th metatarsal heads.
- **Metric Dimension Extraction:** Measures real-world Foot Length ($L_{mm}$) and Foot Width ($W_{mm}$) in millimeters with sub-millimeter accuracy.
- **Cross-Brand Size Recommendation:** Maps calculated dimensions to international shoe sizing standards (EU, US, UK, JP) and brand-specific sizing fits (e.g., Nike, Adidas, Puma).
- **FastAPI REST Service:** Microservice-ready asynchronous API with automated interactive OpenAPI/Swagger documentation.
- **Containerized Infrastructure:** Production-ready Docker configuration for seamless cloud deployments (AWS ECS, GCP Cloud Run, Azure Container Instances).

---

## 💻 Technology Stack

- **Core Programming Language:** Python 3.10+
- **Computer Vision & Image Processing:** OpenCV (`opencv-python`), SciPy, NumPy, scikit-image
- **Machine Learning & Deep Learning:** PyTorch, Torchvision, MediaPipe
- **Web API Framework:** FastAPI, Uvicorn, Pydantic (v2)
- **Deployment & Containerization:** Docker, Docker Compose, Nginx
- **Code Quality & Testing:** Pytest, Flake8, Black

---

## 🔬 System Architecture & CV Pipeline

The FootFit processing pipeline transforms a raw input image into calibrated spatial dimensions and size predictions through five stages:

```
[ Raw Image Input ]
        │
        ▼
┌─────────────────────────┐
│ 1. Quality & Preprocess │  ──> Blur detection, contrast normalization (CLAHE)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 2. Reference Detection  │  ──> Quad contour detection & perspective warping (H)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 3. Foot Segmentation    │  ──> Mask generation & anatomical landmark localization
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 4. Dimension Extraction │  ──> Euclidean distance calculation in real-world metric space
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 5. Size Recommendation  │  ──> Mapping (L_mm, W_mm) -> Standard Sizing Charts
└─────────────────────────┘
```

### Mathematical Pipeline Details

#### 1. Image Quality Validation
Before processing, blur intensity is assessed via the Laplacian variance $\sigma^2$:

$$\sigma^2 = \text{Var}\left(\nabla^2 I\right)$$

If $\sigma^2 < \tau_{blur}$, the request is rejected due to excessive motion blur.

#### 2. Perspective Calibration & Metric Scaling
Four corner coordinates $C_{src} = \{c_1, c_2, c_3, c_4\}$ of a standard reference object of known dimensions ($W_{ref} \times H_{ref}$) are extracted. The Homography transformation matrix $H \in \mathbb{R}^{3 \times 3}$ is calculated using the Direct Linear Transformation (DLT) algorithm:

$$p_{rectified} = H \cdot p_{raw}$$

The Scale Factor ($S_{ppm}$, pixels per millimeter) is derived:

$$S_{ppm} = \frac{\| c_1 - c_2 \|_2}{W_{ref}}$$

#### 3. Spatial Keypoint Extraction
The segmented foot contour yields key anatomical reference points:
- Heel posterior center point: $P_{heel} = (x_h, y_h)$
- Longest toe distal apex: $P_{toe} = (x_t, y_t)$
- 1st Metatarsal head (Medial point): $P_{m1} = (x_{m1}, y_{m1})$
- 5th Metatarsal head (Lateral point): $P_{m5} = (x_{m5}, y_{m5})$

#### 4. Metric Dimension Calculation
Real-world length ($L_{mm}$) and width ($W_{mm}$) are calculated using Euclidean distance scaled by $S_{ppm}$:

$$L_{mm} = \frac{\| P_{toe} - P_{heel} \|_2}{S_{ppm}} = \frac{\sqrt{(x_t - x_h)^2 + (y_t - y_h)^2}}{S_{ppm}}$$

$$W_{mm} = \frac{\| P_{m1} - P_{m5} \|_2}{S_{ppm}} = \frac{\sqrt{(x_{m1} - x_{m5})^2 + (y_{m1} - y_{m5})^2}}{S_{ppm}}$$

---

## 📂 Project Structure

```
footfit/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── config.py                 # Environment configurations & defaults
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── measurement.py    # Route handlers for foot measurement
│   │   │   ├── recommendation.py # Route handlers for shoe size recommendation
│   │   │   └── health.py         # System health check route
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── request.py        # Pydantic request models
│   │       └── response.py       # Pydantic response models
│   ├── cv/
│   │   ├── __init__.py
│   │   ├── preprocessor.py       # Image enhancement & blur detection
│   │   ├── calibration.py        # Homography & reference plane warping
│   │   ├── segmentor.py          # U-Net / DeepLab foot mask generation
│   │   ├── landmark_detector.py  # Keypoint detection (heel, toes, metatarsals)
│   │   └── measurement_engine.py # Metric distance calculation engine
│   └── services/
│       ├── __init__.py
│       └── size_recommender.py   # Brand size matrix matching & fit algorithm
├── assets/
│   ├── sample_images/            # Test input images for calibration
│   └── reference_charts/         # Brand size conversion tables (JSON)
├── docker/
│   ├── Dockerfile                # Production Docker container build definition
│   └── docker-compose.yml        # Docker Compose service configuration
├── tests/
│   ├── test_api.py               # Endpoint testing suite
│   ├── test_cv_pipeline.py       # Computer Vision unit tests
│   └── test_recommender.py       # Recommendation logic tests
├── .env.example                  # Environment variable template
├── .gitignore
├── requirements.txt              # Production Python dependencies
├── requirements-dev.txt          # Development & testing dependencies
└── README.md                     # Project documentation
```

---

## ⚙️ Installation & Setup

### Prerequisites

- **Python:** Version 3.10 or higher
- **Package Manager:** `pip` or `conda`
- **Docker & Docker Compose:** (Optional, for containerized execution)
- **System Dependencies:** `ffmpeg`, `libsm6`, `libxext6` (for OpenCV on Linux)

---

### 1. Local Python Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-organization/footfit.git
   cd footfit
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install system dependencies (Linux users):**
   ```bash
   sudo apt-get update && sudo apt-get install -y libgl1-mesa-glx libglib2.0-0
   ```

4. **Install Python dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Run the FastAPI server locally:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   The application will be accessible at `http://localhost:8000`. Access interactive API documentation at `http://localhost:8000/docs`.

---

### 2. Docker Containerization

1. **Build and start the container using Docker Compose:**
   ```bash
   docker-compose -f docker/docker-compose.yml up --build -d
   ```

2. **Check container status:**
   ```bash
   docker-compose -f docker/docker-compose.yml ps
   ```

3. **View application logs:**
   ```bash
   docker-compose -f docker/docker-compose.yml logs -f footfit-api
   ```

4. **Stop running containers:**
   ```bash
   docker-compose -f docker/docker-compose.yml down
   ```

---

## 📡 API Endpoint Documentation

### Base URL
`http://localhost:8000/api/v1`

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | Service operational health check |
| `/scan/measure` | `POST` | Upload image, calibrate reference object, and compute foot dimensions |
| `/recommend` | `POST` | Input dimensions to retrieve recommended shoe sizes across brands |
| `/scan/process-full` | `POST` | Combined endpoint for measurement extraction and size recommendation |

---

### Endpoint Details & Payload Examples

#### 1. Measure Foot (`POST /api/v1/scan/measure`)

- **Content-Type:** `multipart/form-data`

**Parameters:**
- `file` *(file, required)*: Image file (JPEG/PNG).
- `reference_type` *(string, required)*: Type of reference object (`A4_PAPER`, `CREDIT_CARD`, `CUSTOM`).
- `reference_width_mm` *(float, optional)*: Overrides width if `CUSTOM` reference is chosen.

**Example Response (`200 OK`):**
```json
{
  "status": "success",
  "data": {
    "image_quality": {
      "blur_variance": 342.5,
      "is_valid": true
    },
    "measurements": {
      "length_mm": 268.4,
      "width_mm": 102.1,
      "arch_type": "NORMAL"
    },
    "calibration": {
      "scale_factor_ppm": 3.42,
      "reference_type": "A4_PAPER",
      "confidence_score": 0.98
    },
    "landmarks": {
      "heel": [450, 1200],
      "toe": [452, 280],
      "metatarsal_medial": [320, 750],
      "metatarsal_lateral": [670, 780]
    }
  }
}
```

---

#### 2. Get Recommendation (`POST /api/v1/recommend`)

- **Content-Type:** `application/json`

**Example Request Payload:**
```json
{
  "length_mm": 268.4,
  "width_mm": 102.1,
  "gender": "UNISEX",
  "target_brand": "NIKE",
  "preferred_fit": "REGULAR"
}
```

**Example Response (`200 OK`):**
```json
{
  "status": "success",
  "recommendations": {
    "input_dimensions": {
      "length_mm": 268.4,
      "width_mm": 102.1
    },
    "standard_sizes": {
      "EU": 42.5,
      "US": 9.5,
      "UK": 8.5,
      "CM": 27.0
    },
    "brand_recommendation": {
      "brand": "NIKE",
      "recommended_size_us": 9.5,
      "fit_rating": "TRUE_TO_SIZE",
      "confidence": 0.95,
      "notes": "Optimal fit calculated with 5.6mm toe clearance allowance."
    }
  }
}
```

---

## 🚀 Usage Guide

### Curl Example: Full Foot Scan

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/scan/measure' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@/path/to/foot_sample.jpg;type=image/jpeg' \
  -F 'reference_type=A4_PAPER'
```

### Python SDK Request Example

```python
import requests

url = "http://localhost:8000/api/v1/scan/measure"
payload = {"reference_type": "A4_PAPER"}
files = [("file", ("foot_sample.jpg", open("foot_sample.jpg", "rb"), "image/jpeg"))]

response = requests.post(url, data=payload, files=files)
print(response.json())
```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for complete details.